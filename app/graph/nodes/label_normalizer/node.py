from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Optional, Literal
import logging
import re

from app.models.agentState import AgentState
from app.models.date_labels import DateLabelLiteral
from app.config import get_settings
from app.graph.nodes.label_normalizer.prompt import LABEL_NORMALIZER_PROMPT

logger = logging.getLogger(__name__)


class LabelExtraction(BaseModel):
    """
    Structured output from the label normalizer.
    Extracts date labels and ASIN with self-evaluation.
    """
    
    # Date Labels (primary period)
    date_start_label: DateLabelLiteral = Field(
        description="Label for start date"
    )
    date_end_label: DateLabelLiteral = Field(
        description="Label for end date"
    )
    
    # Date Labels (comparison period - optional)
    compare_date_start_label: Optional[DateLabelLiteral] = Field(
        default=None,
        description="Label for comparison start date"
    )
    compare_date_end_label: Optional[DateLabelLiteral] = Field(
        default=None,
        description="Label for comparison end date"
    )
    
    # Explicit date metadata
    explicit_date_start: Optional[str] = Field(
        default=None,
        description="ISO date if date_start_label is 'explicit_date'"
    )
    explicit_date_end: Optional[str] = Field(
        default=None,
        description="ISO date if date_end_label is 'explicit_date'"
    )
    explicit_compare_start: Optional[str] = Field(
        default=None,
        description="ISO date if compare_date_start_label is 'explicit_date'"
    )
    explicit_compare_end: Optional[str] = Field(
        default=None,
        description="ISO date if compare_date_end_label is 'explicit_date'"
    )
    
    # Custom days count metadata
    custom_days_count: Optional[int] = Field(
        default=None,
        description="Number of days if using 'past_days' label"
    )
    custom_compare_days_count: Optional[int] = Field(
        default=None,
        description="Number of days for comparison if using 'past_days' label"
    )
    
    # ASIN extraction
    asin: Optional[str] = Field(
        default=None,
        description="Amazon ASIN (10-character alphanumeric code)"
    )
    
    # Self-evaluation
    is_valid: bool = Field(
        description="Whether the extraction is valid"
    )
    validation_feedback: Optional[str] = Field(
        default=None,
        description="Feedback on what needs improvement if not valid"
    )


def validate_asin(asin: str) -> bool:
    """
    Validate ASIN format: 10-character alphanumeric code.
    """
    if not asin or len(asin) != 10:
        return False
    return bool(re.match(r'^[A-Z0-9]{10}$', asin.upper()))


def extract_asin_from_text(text: str) -> Optional[str]:
    """
    Extract ASIN from text using regex.
    """
    # Pattern: B followed by 9 alphanumeric characters (most ASINs start with B)
    pattern = r'\b(B[A-Z0-9]{9})\b'
    match = re.search(pattern, text.upper())
    if match:
        return match.group(1)
    
    # Fallback: any 10-character alphanumeric code
    pattern = r'\b([A-Z0-9]{10})\b'
    match = re.search(pattern, text.upper())
    if match:
        potential_asin = match.group(1)
        if validate_asin(potential_asin):
            return potential_asin
    
    return None


def label_normalizer_node(state: AgentState) -> AgentState:
    """
    FIRST NODE: Extracts date labels and ASIN with self-evaluation and retry.
    
    Features:
    - Extracts date labels for primary and comparison periods
    - Extracts ASIN (if present)
    - Self-evaluates the extraction
    - Retries up to 3 times if extraction is not valid
    """
    
    question = state["question"]
    logger.info(f"🔍 Extracting labels from: '{question}'")
    
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key
    )
    
    # Bind structured output
    llm_with_structure = llm.with_structured_output(LabelExtraction)
    
    max_retries = 3
    retry_count = 0
    feedback = "First attempt - no feedback yet."
    extraction = None
    
    while retry_count < max_retries:
        logger.info(f"🔄 Extraction attempt {retry_count + 1}/{max_retries}")
        
        # Create prompt with feedback
        prompt = LABEL_NORMALIZER_PROMPT.format(
            question=question,
            feedback=feedback
        )
        
        try:
            extraction = llm_with_structure.invoke(prompt)
            
            # Validate ASIN if extracted
            if extraction.asin:
                # Try to extract from original text first (more reliable)
                extracted_asin = extract_asin_from_text(question)
                if extracted_asin:
                    extraction.asin = extracted_asin
                    logger.info(f"📦 ASIN found: {extraction.asin}")
                elif not validate_asin(extraction.asin):
                    logger.warning(f"❌ Invalid ASIN format: {extraction.asin}, setting to None")
                    extraction.asin = None
            
            # Check if extraction is valid
            if extraction.is_valid:
                logger.info(f"✅ Extraction valid on attempt {retry_count + 1}")
                break
            else:
                retry_count += 1
                feedback = extraction.validation_feedback or "Extraction not valid, please try again."
                logger.warning(f"⚠️ Extraction not valid: {feedback}")
                
                if retry_count >= max_retries:
                    logger.warning(f"❌ Max retries reached, using last extraction")
                    break
                    
        except Exception as e:
            logger.error(f"❌ Error extracting labels: {e}")
            retry_count += 1
            feedback = f"Error occurred: {str(e)}. Please try again."
            
            if retry_count >= max_retries:
                logger.error("❌ Max retries reached with errors, using defaults")
                # Fallback to safe defaults
                state["_date_start_label"] = "default"
                state["_date_end_label"] = "default"
                state["_compare_date_start_label"] = None
                state["_compare_date_end_label"] = None
                state["_explicit_date_start"] = None
                state["_explicit_date_end"] = None
                state["_explicit_compare_start"] = None
                state["_explicit_compare_end"] = None
                state["_custom_days_count"] = None
                state["_custom_compare_days_count"] = None
                state["asin"] = None
                state["_normalizer_valid"] = False
                state["_normalizer_retries"] = retry_count
                state["_normalizer_feedback"] = feedback
                return state
    
    # Update state with extracted information
    if extraction:
        state["_date_start_label"] = extraction.date_start_label
        state["_date_end_label"] = extraction.date_end_label
        state["_compare_date_start_label"] = extraction.compare_date_start_label
        state["_compare_date_end_label"] = extraction.compare_date_end_label
        
        # Metadata for explicit dates
        state["_explicit_date_start"] = extraction.explicit_date_start
        state["_explicit_date_end"] = extraction.explicit_date_end
        state["_explicit_compare_start"] = extraction.explicit_compare_start
        state["_explicit_compare_end"] = extraction.explicit_compare_end
        
        # Metadata for custom days
        state["_custom_days_count"] = extraction.custom_days_count
        state["_custom_compare_days_count"] = extraction.custom_compare_days_count
        
        # ASIN
        state["asin"] = extraction.asin
        
        # Validation metadata
        state["_normalizer_valid"] = extraction.is_valid
        state["_normalizer_retries"] = retry_count
        state["_normalizer_feedback"] = extraction.validation_feedback
        
        logger.info(f"📊 Extracted labels: start={extraction.date_start_label}, end={extraction.date_end_label}")
        if extraction.compare_date_start_label:
            logger.info(f"📊 Comparison labels: start={extraction.compare_date_start_label}, end={extraction.compare_date_end_label}")
        logger.info(f"✅ Extraction completed with {retry_count} retries")
    
    return state

