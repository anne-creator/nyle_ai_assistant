from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import tool
from typing import List
import logging

from app.models.agentState import AgentState
from app.config import get_settings
from app.graph.nodes.metrics_query_handler.prompt import METRICS_QUERY_SYSTEM_PROMPT
from app.graph.nodes.metrics_query_handler.simple_metrics_tool import get_simple_metrics
from app.metricsAccessLayer import metrics_api
from app.context import set_jwt_token_for_task

logger = logging.getLogger(__name__)

# Store state for tool access
_current_state = {}


async def metrics_query_handler_node(state: AgentState) -> AgentState:
    """
    Handler for metrics_query type questions.
    
    Handles questions like:
    - "What is my ACOS?"
    - "Show me total sales"
    - "Give me store overview"
    """
    global _current_state
    _current_state = state
    
    # Ensure JWT token is available for async tasks
    set_jwt_token_for_task(state["_jwt_token"])
    
    logger.info(f"Processing metrics_query: '{state['question']}'")
    
    settings = get_settings()
    
    @tool
    async def get_ads_metrics() -> dict:
        """Fetch advertising metrics from Nyle backend.
        
        Returns advertising performance data including ACOS, ad spend, sales, etc.
        """
        logger.info("Tool: get_ads_metrics")
        
        result = await metrics_api.get_ads_executive_summary(
            _current_state["date_start"],
            _current_state["date_end"]
        )
        
        logger.info("Retrieved ads metrics")
        return result
    
    @tool
    async def get_financial_metrics() -> dict:
        """Fetch financial metrics from Nyle backend.
        
        Returns financial data including profit, revenue, expenses, etc.
        """
        logger.info("Tool: get_financial_metrics")
        
        result = await metrics_api.get_financial_summary(
            _current_state["date_start"],
            _current_state["date_end"]
        )
        
        logger.info("Retrieved financial metrics")
        return result
    
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key
    )
    
    agent = create_agent(
        llm,
        tools=[get_simple_metrics],
        system_prompt=METRICS_QUERY_SYSTEM_PROMPT
    )
    
    logger.info("Running metrics query agent...")
    
    result = await agent.ainvoke(
        {"messages": [(
            "human",
            f"Question: {state['question']}\nDate: {state['date_start']} to {state['date_end']}"
        )]},
        config={"recursion_limit": 10}
    )
    
    state["response"] = result["messages"][-1].content
    logger.info("Generated response")
    
    return state
