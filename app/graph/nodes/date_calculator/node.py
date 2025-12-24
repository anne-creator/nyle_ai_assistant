import logging
from datetime import datetime, timezone

from app.models.agentState import AgentState
from app.utils.date_calculator import DateCalculator

logger = logging.getLogger(__name__)


def date_calculator_node(state: AgentState) -> AgentState:
    """
    Calculate actual ISO dates from extracted date labels.
    
    Uses the DateCalculator utility to convert labels like:
    - "yesterday" → "2025-12-23"
    - "past_7_days" → ("2025-12-17", "2025-12-24")
    - "explicit_date" + metadata → specific date
    """
    
    logger.info("📅 Calculating dates from labels")
    
    # Initialize calculator with current date
    calculator = DateCalculator()
    
    # Get extracted labels from state
    date_start_label = state.get("_date_start_label")
    date_end_label = state.get("_date_end_label")
    compare_start_label = state.get("_compare_date_start_label")
    compare_end_label = state.get("_compare_date_end_label")
    
    # Get metadata
    explicit_start = state.get("_explicit_date_start")
    explicit_end = state.get("_explicit_date_end")
    explicit_compare_start = state.get("_explicit_compare_start")
    explicit_compare_end = state.get("_explicit_compare_end")
    custom_days = state.get("_custom_days_count")
    
    try:
        # Calculate primary date range (REQUIRED)
        if date_start_label and date_end_label:
            start_date, _ = calculator.calculate(
                label=date_start_label,
                explicit_date=explicit_start,
                custom_days=custom_days
            )
            _, end_date = calculator.calculate(
                label=date_end_label,
                explicit_date=explicit_end,
                custom_days=custom_days
            )
            
            state["date_start"] = start_date
            state["date_end"] = end_date
            logger.info(f"✅ Primary range: {start_date} to {end_date}")
        else:
            # Fallback to default (past 7 days)
            logger.warning("⚠️ No date labels found, using default (past_7_days)")
            start_date, end_date = calculator.calculate("default")
            state["date_start"] = start_date
            state["date_end"] = end_date
        
        # Calculate comparison date range (OPTIONAL)
        if compare_start_label and compare_end_label:
            compare_start, _ = calculator.calculate(
                label=compare_start_label,
                explicit_date=explicit_compare_start,
                custom_days=state.get("_custom_compare_days_count")
            )
            _, compare_end = calculator.calculate(
                label=compare_end_label,
                explicit_date=explicit_compare_end,
                custom_days=state.get("_custom_compare_days_count")
            )
            
            state["compare_date_start"] = compare_start
            state["compare_date_end"] = compare_end
            logger.info(f"✅ Comparison range: {compare_start} to {compare_end}")
        else:
            state["compare_date_start"] = None
            state["compare_date_end"] = None
    
    except Exception as e:
        logger.error(f"❌ Error calculating dates: {e}")
        # Fallback to safe default
        start_date, end_date = calculator.calculate("default")
        state["date_start"] = start_date
        state["date_end"] = end_date
        state["compare_date_start"] = None
        state["compare_date_end"] = None
    
    return state

