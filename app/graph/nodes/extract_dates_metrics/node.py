from langchain_openai import ChatOpenAI
from datetime import datetime
import logging

from app.models.state import AgentState
from app.models.extraction import DateRange
from app.config import get_settings
from app.graph.nodes.extract_dates_metrics.prompt import EXTRACT_DATES_METRICS_PROMPT
from app.graph.nodes.extract_dates_metrics.date_utils import try_pattern_matching

logger = logging.getLogger(__name__)


def extract_dates_metrics_node(state: AgentState) -> AgentState:
    """
    Extract date range for metrics_query type questions.
    
    This handles single-period questions like:
    - "What is my ACOS?"
    - "Show me last month's sales"
    """
    
    logger.info("Extracting dates for metrics_query")
    
    # If dates already provided by frontend, skip
    if state.get("date_start") and state.get("date_end"):
        logger.info("Dates already provided, skipping extraction")
        return state
    
    question = state["question"]
    current_date = datetime.now().date()
    
    # Try pattern matching first (for relative dates like "last 7 days", "today", etc.)
    date_range = try_pattern_matching(question, current_date)
    
    if date_range:
        # Pre-processor successfully matched a pattern
        state["date_start"] = date_range[0]
        state["date_end"] = date_range[1]
        logger.info(f"Pre-processor extracted: {state['date_start']} to {state['date_end']}")
    else:
        # No pattern matched - question has explicit dates, use LLM
        settings = get_settings()
        llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0,
            api_key=settings.openai_api_key
        ).with_structured_output(DateRange)
        
        current_date_str = current_date.strftime("%Y-%m-%d")
        prompt = EXTRACT_DATES_METRICS_PROMPT.format(
            current_date=current_date_str,
            question=question
        )
        
        dates = llm.invoke(prompt)
        
        state["date_start"] = dates.date_start
        state["date_end"] = dates.date_end
        
        logger.info(f"LLM extracted: {state['date_start']} to {state['date_end']}")
    
    return state
