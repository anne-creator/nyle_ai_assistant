"""Dashboard Load Handler Node."""
import logging
from app.models.agentState import AgentState

logger = logging.getLogger(__name__)


async def dashboard_load_handler_node(state: AgentState) -> AgentState:
    """
    Handler for dashboard_load interaction type.
    
    Currently returns simple greeting.
    Future: Can fetch live data (product count, recent sales, alerts, etc.)
    """
    logger.info("Processing dashboard_load interaction")
    
    # Simple greeting for now
    state["response"] = "Your products dashboard is ready! Ask me anything about your products."
    
    # Future enhancement: fetch live dashboard summary
    # total_products = await products_api.get_product_count()
    # recent_sales = await metrics_api.get_today_sales()
    # state["response"] = f"Welcome! You have {total_products} products. Today's sales: ${recent_sales}"
    
    return state

