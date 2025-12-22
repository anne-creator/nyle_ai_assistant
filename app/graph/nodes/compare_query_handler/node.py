from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
import logging

from app.models.state import AgentState
from app.config import get_settings
from app.metricsAccessLayer import metrics_api
from app.graph.nodes.compare_query_handler.prompt import COMPARISON_QUERY_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Store state for tool access
_current_state = {}


def compare_query_handler_node(state: AgentState) -> AgentState:
    """
    Handler for compare_query type questions.
    
    Handles questions like:
    - "Compare August vs September"
    - "How did sales change from Q1 to Q2?"
    """
    global _current_state
    _current_state = state
    
    logger.info(f"Processing compare_query: '{state['question']}'")
    
    settings = get_settings()
    
    @tool
    async def get_ads_comparison() -> dict:
        """Fetch advertising metrics for two periods for comparison.
        
        Returns ads data for both the current and comparison periods.
        """
        logger.info("Tool: get_ads_comparison")
        
        # Fetch current period
        current = await metrics_api.get_ads_executive_summary(
            _current_state["date_start"],
            _current_state["date_end"]
        )
        
        # Fetch comparison period
        comparison = await metrics_api.get_ads_executive_summary(
            _current_state["compare_date_start"],
            _current_state["compare_date_end"]
        )
        
        logger.info("Retrieved comparison data")
        return {
            "current": current,
            "comparison": comparison
        }
    
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key
    )
    
    agent = create_react_agent(
        llm,
        tools=[get_ads_comparison],
        prompt=COMPARISON_QUERY_SYSTEM_PROMPT
    )
    
    logger.info("Running comparison query agent...")
    
    result = agent.invoke({
        "messages": [(
            "human",
            f"""Question: {state['question']}

Current period: {state['date_start']} to {state['date_end']}
Comparison period: {state['compare_date_start']} to {state['compare_date_end']}

Use get_ads_comparison to fetch data for both periods and provide a comparison."""
        )]
    })
    
    state["response"] = result["messages"][-1].content
    logger.info("Generated comparison response")
    
    return state
