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
    state["response"] = """Here is your store overview (Sep 1-14, 2025):
• Total Sales: $1,935,035
• Net Profit: $313,828
  Net Margin : $
• ROI: 17%

**Store Insights:**
• Strongest performance happens during Sep 01-05, 2025 and this is because you set your **ACOS** (advertising cost of sale) as **20%** at that time
• Your net profit peaks around Sep 01-05, 2025 and declines afterwards, and this is because you set your **TOS IS** (Top of Search Impression Share) to **15%** on Sep 07, 2025

**Your store also has a huge potential:**
You could have been made **$75,318** (**net profit loss**) (that's a **24% increase**) from Sep 01 to Sep 14, 2025, if you adjusted your ACOS to 20% and TOS IS to 7-8% at Sep 01, 2025.

**It's not too late, here is the goal setting you can apply today!**
👉ACoS = 20%
👉TOS IS = 7-8%
After we set the goal, the **Net Profit** is going to increase by **$15,000** in the next month!"""
    
    return state

