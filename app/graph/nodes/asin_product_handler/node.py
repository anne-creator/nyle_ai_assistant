"""
ASIN Product Handler Node.

Handles ASIN-level queries including:
- Single ASIN metrics
- Ranking queries (top/bottom N)
- Simple ASIN metrics
"""

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
import logging

from app.models.agentState import AgentState
from app.config import get_settings
from app.graph.nodes.asin_product_handler.prompt import ASIN_PRODUCT_SYSTEM_PROMPT
from app.graph.nodes.asin_product_handler.templates import format_templates_for_prompt
from app.graph.nodes.asin_product_handler.asin_metrics_tool import (
    get_ranked_products,
    get_asin_metrics,
)
from app.context import set_jwt_token_for_task

logger = logging.getLogger(__name__)


async def asin_product_handler_node(state: AgentState) -> AgentState:
    """
    Handler for asin_product type questions.
    
    Handles ASIN-specific questions like:
    - "What are sales for ASIN B0B5HN65QQ?"
    - "What are my top 5 selling ASINs?"
    - "Which product has the highest ROI?"
    """
    
    # Ensure JWT token is available for async tasks
    set_jwt_token_for_task(state["_jwt_token"])
    
    logger.info(f"Processing asin_product query: '{state['question']}'")
    logger.info(f"ASIN: {state.get('asin', 'N/A')}")
    logger.info(f"Date: {state['date_start']} to {state['date_end']}")
    
    settings = get_settings()
    
    # Build prompt with templates injected
    prompt_with_templates = ASIN_PRODUCT_SYSTEM_PROMPT.format(
        templates=format_templates_for_prompt()
    )
    
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key
    )
    
    # Create agent with ASIN-aware tools
    agent = create_agent(
        llm,
        tools=[get_ranked_products, get_asin_metrics],
        system_prompt=prompt_with_templates
    )
    
    logger.info("Running ASIN product query agent...")
    
    # Build the message with context
    asin_info = f"ASIN: {state['asin']}" if state.get('asin') else "ASIN: Not specified (use get_ranked_products for ranking queries)"
    date_start = state['date_start']
    date_end = state['date_end']
    
    result = await agent.ainvoke(
        {"messages": [(
            "human",
            f"Question: {state['question']}\n"
            f"{asin_info}\n"
            f"date_start: {date_start}\n"
            f"date_end: {date_end}\n"
            f"\nUse these exact date values when calling tools."
        )]},
        config={"recursion_limit": 10}
    )
    
    state["response"] = result["messages"][-1].content
    logger.info("Generated ASIN product response")
    
    return state
