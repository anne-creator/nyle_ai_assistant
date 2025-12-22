from langchain_openai import ChatOpenAI
from datetime import datetime
import logging

from app.models.state import AgentState
from app.models.extraction import AsinDateRange
from app.config import get_settings
from app.graph.nodes.extract_dates_asin.prompt import EXTRACT_DATES_ASIN_PROMPT

logger = logging.getLogger(__name__)


def extract_dates_asin_node(state: AgentState) -> AgentState:
    """
    Extract date range AND ASIN for asin_product type questions.
    
    This handles ASIN-specific questions like:
    - "What are sales for ASIN B0B5HN65QQ?"
    - "When will product B0DP55J8ZG go out of stock?"
    """
    
    logger.info("Extracting dates and ASIN for asin_product query")
    
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key
    ).with_structured_output(AsinDateRange)
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    prompt = EXTRACT_DATES_ASIN_PROMPT.format(
        current_date=current_date,
        question=state["question"]
    )
    
    result = llm.invoke(prompt)
    
    state["asin"] = result.asin
    state["date_start"] = result.date_start
    state["date_end"] = result.date_end
    
    logger.info(f"ASIN: {state['asin']}")
    logger.info(f"Date range: {state['date_start']} to {state['date_end']}")
    
    return state
