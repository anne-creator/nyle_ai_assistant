"""
Inventory Handler Node - COO inventory management and DOI analysis.

Handles questions about:
- Days of Inventory (DOI)
- Storage fees and costs
- Stockout risks and low stock alerts
"""

import logging
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

from app.models.agentState import AgentState
from app.config import get_settings
from app.context import set_jwt_token_for_task
from .prompt import INVENTORY_HANDLER_SYSTEM_PROMPT
from .inventory_tools import (
    get_current_doi,
    get_doi_trend,
    get_storage_fees_summary,
    get_storage_fees_trend,
    get_low_stock_asins
)

logger = logging.getLogger(__name__)


async def inventory_handler_node(state: AgentState) -> AgentState:
    """
    Handler for inventory_query type questions.
    
    Handles questions like:
    - "What's the DOI today?"
    - "How has my DOI trended over the last 30 days?"
    - "What's the Storage Fees last 30 days?"
    - "Which ASINs have less than 30 days of stock left?"
    """
    
    # Ensure JWT token is available for async tasks
    set_jwt_token_for_task(state["_jwt_token"])
    
    question = state["question"]
    date_start = state["date_start"]
    date_end = state["date_end"]
    asin = state.get("asin")
    
    # Override "today" with November 1, 2025 for inventory queries (demo data date)
    # Only apply when user explicitly asks for "today"
    TODAY_OVERRIDE = "2025-10-01"
    
    question_lower = question.lower()
    if "today" in question_lower and date_start == date_end:
        logger.info(f"Overriding 'today' date from {date_start} to {TODAY_OVERRIDE}")
        date_start = TODAY_OVERRIDE
        date_end = TODAY_OVERRIDE
    
    logger.info(f"Processing inventory_query: '{question}'")
    logger.info(f"Date range: {date_start} to {date_end}, ASIN: {asin or 'All'}")
    
    settings = get_settings()
    
    # Create LLM
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key,
        streaming=True
    )
    
    # Create agent with inventory tools
    agent = create_agent(
        llm,
        tools=[
            get_current_doi,
            get_doi_trend,
            get_storage_fees_summary,
            get_storage_fees_trend,
            get_low_stock_asins
        ],
        system_prompt=INVENTORY_HANDLER_SYSTEM_PROMPT
    )
    
    logger.info("Running inventory query agent...")
    
    # Build the message with context
    asin_info = f"ASIN: {asin}" if asin else "ASIN: All products"
    
    result = await agent.ainvoke(
        {"messages": [(
            "human",
            f"Question: {question}\n"
            f"date_start: {date_start}\n"
            f"date_end: {date_end}\n"
            f"{asin_info}\n"
            f"\nUse these exact date values when calling tools. "
            f"If the question asks for 'today', use date_start as today's date."
        )]},
        config={"recursion_limit": 10}
    )
    
    state["response"] = result["messages"][-1].content
    logger.info("Generated inventory response")
    
    return state
