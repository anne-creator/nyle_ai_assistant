import logging
from datetime import datetime, timezone

from app.models.agentState import AgentState
from app.utils.date_calculator import DateCalculator

logger = logging.getLogger(__name__)


def message_analyzer_node(state: AgentState) -> AgentState:
    """
    Message analyzer (Node 2): Converts date labels to actual ISO dates.
    
    This is a pure Python deterministic node (no AI/LLM calls).
    
    Inputs (from Node 1 - label_normalizer):
        - _date_start_label, _date_end_label
        - _compare_date_start_label, _compare_date_end_label
        - _explicit_date_start, _explicit_date_end
        - _explicit_compare_start, _explicit_compare_end
        - _custom_days_count, _custom_compare_days_count
    
    Outputs:
        - date_start, date_end (ISO format: YYYY-MM-DD)
        - compare_date_start, compare_date_end (optional)
    
    Date Label Rules:
        - "this_week": Monday to Sunday (full calendar week)
        - "this_month": First day to last day of month (full month)
        - "mtd": First day of month to today (Month-to-Date)
        - "past_X_days": Inclusive dates (end=today, start=today-X+1)
        - "explicit_date": Maps directly from _explicit_date_start/end
    """
    
    logger.info("📅 Message Analyzer: Calculating dates from labels")
    
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

