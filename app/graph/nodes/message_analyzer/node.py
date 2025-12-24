from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Optional, Literal
import logging
import re

from app.models.agentState import AgentState
from app.models.date_labels import DateLabelLiteral
from app.config import get_settings
from app.graph.nodes.message_analyzer.prompt import MESSAGE_ANALYZER_PROMPT

logger = logging.getLogger(__name__)


class MessageAnalysis(BaseModel):
    """
    Structured output from the message analyzer.
    Combines date labels, ASIN extraction, and question classification.
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
    
    # ASIN extraction
    asin: Optional[str] = Field(
        default=None,
        description="Amazon ASIN (10-character alphanumeric code)"
    )
    
    # Question classification
    question_type: Literal["metrics_query", "compare_query", "asin_product", "hardcoded"] = Field(
        description="Type of question for routing"
    )


def validate_asin(asin: str) -> bool:
    """
    Validate ASIN format: 10-character alphanumeric code.
    
    Amazon ASINs follow this pattern:
    - Exactly 10 characters
    - Alphanumeric only (A-Z, 0-9)
    - Usually starts with 'B'
    """
    if not asin or len(asin) != 10:
        return False
    return bool(re.match(r'^[A-Z0-9]{10}$', asin.upper()))


def extract_asin_from_text(text: str) -> Optional[str]:
    """
    Extract ASIN from text using regex.
    Looks for 10-character alphanumeric codes.
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


def message_analyzer_node(state: AgentState) -> AgentState:
    """
    FIRST NODE: Analyzes user message and extracts:
    1. Date labels (from date_labels.py)
    2. ASIN (if present)
    3. Question type (for routing)
    
    This node sets up all the critical state for downstream nodes.
    """
    
    question = state["question"]
    logger.info(f"🔍 Analyzing message: '{question}'")
    
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key
    )
    
    # Bind structured output
    llm_with_structure = llm.with_structured_output(MessageAnalysis)
    
    # Create prompt
    prompt = MESSAGE_ANALYZER_PROMPT.format(question=question)
    
    # Invoke LLM
    try:
        analysis: MessageAnalysis = llm_with_structure.invoke(prompt)
        logger.info(f"✅ Analysis complete")
        
        # Validate ASIN if extracted
        if analysis.asin:
            # Try to extract from original text first (more reliable)
            extracted_asin = extract_asin_from_text(question)
            if extracted_asin:
                analysis.asin = extracted_asin
                logger.info(f"📦 ASIN found: {analysis.asin}")
            elif not validate_asin(analysis.asin):
                logger.warning(f"❌ Invalid ASIN format: {analysis.asin}, setting to None")
                analysis.asin = None
        
        # Re-evaluate question type if ASIN found
        if analysis.asin:
            # If ASIN is present and it's not a comparison, classify as asin_product
            if analysis.question_type == "metrics_query":
                analysis.question_type = "asin_product"
                logger.info(f"🔄 Re-classified to 'asin_product' due to ASIN presence")
        
        # Update state with extracted information
        state["_date_start_label"] = analysis.date_start_label
        state["_date_end_label"] = analysis.date_end_label
        state["_compare_date_start_label"] = analysis.compare_date_start_label
        state["_compare_date_end_label"] = analysis.compare_date_end_label
        
        # Metadata for explicit dates
        state["_explicit_date_start"] = analysis.explicit_date_start
        state["_explicit_date_end"] = analysis.explicit_date_end
        state["_explicit_compare_start"] = analysis.explicit_compare_start
        state["_explicit_compare_end"] = analysis.explicit_compare_end
        
        # Metadata for custom days
        state["_custom_days_count"] = analysis.custom_days_count
        
        # ASIN
        state["asin"] = analysis.asin
        
        # Question type
        state["question_type"] = analysis.question_type
        
        logger.info(f"📊 Extracted labels: start={analysis.date_start_label}, end={analysis.date_end_label}")
        if analysis.compare_date_start_label:
            logger.info(f"📊 Comparison labels: start={analysis.compare_date_start_label}, end={analysis.compare_date_end_label}")
        logger.info(f"🎯 Question type: {analysis.question_type}")
        
    except Exception as e:
        logger.error(f"❌ Error analyzing message: {e}")
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
        state["asin"] = None
        state["question_type"] = "metrics_query"
    
    return state

