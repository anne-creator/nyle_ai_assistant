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
    Extracts date labels and ASIN.
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
    FIRST NODE: Extracts date labels and ASIN from user question.
    
    Features:
    - Extracts date labels for primary and comparison periods
    - Extracts ASIN (if present)
    - Validates and corrects ASIN using regex
    - Supports feedback-driven regeneration from Node 3 evaluator
    """
    
    question = state["question"]
    
    # Check if this is a retry with feedback
    feedback = state.get("_normalizer_feedback")
    retry_count = state.get("_normalizer_retries", 0)
    
    if feedback and retry_count > 0:
        logger.info(f"🔄 Retry attempt #{retry_count}: Re-extracting labels with feedback")
        logger.info(f"💡 Feedback: {feedback}")
    else:
        logger.info(f"🔍 Extracting labels from: '{question}'")
    
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key
    )
    
    # Bind structured output
    llm_with_structure = llm.with_structured_output(LabelExtraction)
    
    # Get current year for explicit dates
    from datetime import datetime
    current_year = datetime.now().year
    
    # Build feedback section for prompt
    if feedback and retry_count > 0:
        feedback_section = f"""
⚠️ **CORRECTION REQUIRED** (Retry #{retry_count})
The previous extraction had issues. Please fix them:

{feedback}

**Pay close attention to the feedback above and correct the extraction accordingly.**
"""
        feedback_reminder = f"\n9. **IMPORTANT**: Address the feedback above - {feedback}"
    else:
        feedback_section = "No previous feedback (first attempt)."
        feedback_reminder = ""
    
    # Create prompt with feedback
    prompt = LABEL_NORMALIZER_PROMPT.format(
        question=question,
        current_year=current_year,
        feedback_section=feedback_section,
        feedback_reminder=feedback_reminder
    )
    
    try:
        extraction = llm_with_structure.invoke(prompt)
        
        # Adjust explicit dates if they're in the future (map to previous year)
        def adjust_future_date(date_str: str) -> str:
            """If date is in the future, adjust to previous year."""
            if not date_str:
                return date_str
            
            try:
                from datetime import datetime
                from zoneinfo import ZoneInfo
                
                pst_tz = ZoneInfo("America/Los_Angeles")
                current_date = datetime.now(pst_tz).date()
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                
                # If the date is in the future, use previous year
                if date_obj > current_date:
                    adjusted_year = date_obj.year - 1
                    adjusted_date = date_obj.replace(year=adjusted_year)
                    logger.info(f"📅 Adjusted future date {date_str} → {adjusted_date.strftime('%Y-%m-%d')}")
                    return adjusted_date.strftime("%Y-%m-%d")
                
                return date_str
            except Exception as e:
                logger.warning(f"⚠️ Could not adjust date {date_str}: {e}")
                return date_str
        
        # Apply adjustment to all explicit dates
        if extraction.date_start_label == "explicit_date":
            extraction.explicit_date_start = adjust_future_date(extraction.explicit_date_start)
        if extraction.date_end_label == "explicit_date":
            extraction.explicit_date_end = adjust_future_date(extraction.explicit_date_end)
        if extraction.compare_date_start_label == "explicit_date":
            extraction.explicit_compare_start = adjust_future_date(extraction.explicit_compare_start)
        if extraction.compare_date_end_label == "explicit_date":
            extraction.explicit_compare_end = adjust_future_date(extraction.explicit_compare_end)
        
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
        
        logger.info(f"✅ Extraction completed")
                
    except Exception as e:
        logger.error(f"❌ Error extracting labels: {e}")
        # Return state with error indication
        state["_normalizer_valid"] = False
        state["_normalizer_retries"] = 0
        state["_normalizer_feedback"] = f"Error: {str(e)}"
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
        
        # Don't set validation metadata here - Node 3 will handle it
        # Just clear any old feedback if this is first attempt
        if retry_count == 0:
            state["_normalizer_valid"] = None
            state["_normalizer_retries"] = 0
            state["_normalizer_feedback"] = None
        
        logger.info(f"📊 Extracted labels: start={extraction.date_start_label}, end={extraction.date_end_label}")
        if extraction.compare_date_start_label:
            logger.info(f"📊 Comparison labels: start={extraction.compare_date_start_label}, end={extraction.compare_date_end_label}")
    
    return state

