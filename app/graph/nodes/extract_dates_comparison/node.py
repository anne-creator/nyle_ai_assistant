from langchain_openai import ChatOpenAI
from datetime import datetime
import logging

from app.models.state import AgentState
from app.models.extraction import ComparisonDateRange
from app.config import get_settings
from app.graph.nodes.extract_dates_comparison.prompt import EXTRACT_DATES_COMPARISON_PROMPT

logger = logging.getLogger(__name__)


def extract_dates_comparison_node(state: AgentState) -> AgentState:
    """
    Extract TWO date ranges for compare_query type questions.
    
    This handles comparison questions like:
    - "Compare August vs September"
    - "How did sales change from Q1 to Q2?"
    """
    
    logger.info("Extracting dates for compare_query")
    
    # If dates already provided by frontend, skip
    if (state.get("date_start") and state.get("date_end") and 
        state.get("compare_date_start") and state.get("compare_date_end")):
        logger.info("Dates already provided, skipping extraction")
        return state
    
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key
    ).with_structured_output(ComparisonDateRange)
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    prompt = EXTRACT_DATES_COMPARISON_PROMPT.format(
        current_date=current_date,
        question=state["question"]
    )
    
    dates = llm.invoke(prompt)
    
    state["date_start"] = dates.date_start
    state["date_end"] = dates.date_end
    state["compare_date_start"] = dates.compare_date_start
    state["compare_date_end"] = dates.compare_date_end
    
    logger.info(f"Current period: {state['date_start']} to {state['date_end']}")
    logger.info(f"Compare period: {state['compare_date_start']} to {state['compare_date_end']}")
    
    return state
