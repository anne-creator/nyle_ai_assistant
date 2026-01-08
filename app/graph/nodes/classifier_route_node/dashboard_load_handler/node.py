"""Dashboard Load Handler Node."""
import logging
from app.models.agentState import AgentState

logger = logging.getLogger(__name__)


async def dashboard_load_handler_node(state: AgentState) -> AgentState:
    """
    Handler for dashboard_load interaction type.
    
    Returns hardcoded store overview and insights.
    """
    logger.info("Processing dashboard_load interaction")
    
    # Hardcoded dashboard message
    state["response"] = """Welcome to Nyle. We are the world's first AI-powered Operating System for Autonomous eCommerce Development."""
    
    return state

