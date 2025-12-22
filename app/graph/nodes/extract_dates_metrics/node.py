from langchain_openai import ChatOpenAI
from datetime import datetime
import logging

from app.models.state import AgentState
from app.models.extraction import DateRange
from app.config import get_settings
from app.graph.nodes.extract_dates_metrics.prompt import EXTRACT_DATES_METRICS_PROMPT

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
    
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key
    ).with_structured_output(DateRange)
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    prompt = EXTRACT_DATES_METRICS_PROMPT.format(
        current_date=current_date,
        question=state["question"]
    )
    
    dates = llm.invoke(prompt)
    
    state["date_start"] = dates.date_start
    state["date_end"] = dates.date_end
    
    logger.info(f"Extracted: {state['date_start']} to {state['date_end']}")
    
    return state
