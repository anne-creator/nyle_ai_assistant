import logging

from app.models.agentState import AgentState

logger = logging.getLogger(__name__)


def hardcoded_response_node(state: AgentState) -> AgentState:
    """
    Handler for hardcoded responses (special questions).
    
    Handles:
    - Performance insights
    - Highest performance day
    - Other pre-defined responses
    """
    
    logger.info(f"Processing hardcoded query: '{state['question']}'")
    
    question_lower = state["question"].lower().strip()

    if "show me some insights about this product from oct 1 to oct 30" in question_lower:
        state["response"] = """Performance Insights

I've conducted a comprehensive analysis of your store's performance data spanning from October 1, 2025 to October 31, 2025 for asin B0160HYB8S. I'd like to share some important findings with you:

The Good News:Your net profit was increasing from Oct 1 to Oct 15, 2025 with a total of $78791.98, and this is because you set the ACOS goal from Oct 1 to Oct 15. This consistent cost efficiency created a highly favorable environment for net profit optimization, where your advertising spend remained well-balanced against revenue generation.

Areas of Concern: Your net profit was decreasing from Oct 18 to Oct 29, 2025 with a total of $21070.06, and this is because you were aiming to achieve a goal of your AD TOS IS at 20% from October 15th through October 30th. This increase in impression share, while boosting visibility, created an imbalance in your cost structure where advertising costs outpaced sales growth, leading to a decline in profitability.

Your store has an optimal potential: You could have earned an additional $1121.34 in net profit during this period. This figure represents the difference between your actual earnings and what would have been possible if your key metrics had remained at their optimal levels from October 1, 2025 to October 31, 2025.

Looking ahead, I want to help you recapture that early October momentum and stabilize your business performance. Based on scenario simulations combining your historical data patterns with predictive modeling.

Recommended goals (Nov 1-15, 2025):
ACOS: 23%

Would you like me to update this goal for you?"""

    elif question_lower == "yes":
        state["response"] = """You're goal for Nov 1-15, 2025 is set to
ACOS: 23%"""

    elif "compare my store performance in august over august to september" in question_lower:
        state["response"] = """Performance Insights:

Strongest improvement happens during Sep 01 to 05, 2025 and this is because you optimized your ACOS (advertising cost of sale) to 20% during that period
Your net profit increased by 9.2% from August to September, and this is because you reduced your TOS IS (Top of Search Impression Share) from 18% in late August to 15% on Sep 07, 2025

Your store also has optimization potential:
You could have made $48,290 (net profit gain) (that's a 15% increase) from Aug 15 to Sep 30, 2025, if you had adjusted your ACOS to 20% and TOS IS to 7.8% at Aug 15, 2025"""

    elif "performance insight" in question_lower or "performance compare" in question_lower:
        state["response"] = """Performance Insights:

- Strongest improvement during Sep 01-05, 2025 (optimized ACOS to 20%)
- Net profit increased 9.2% from August to September (reduced TOS IS from 18% to 15%)

Optimization potential: You could have made $48,290 additional net profit (15% increase) from Aug 15 to Sep 30, 2025, if you had adjusted ACOS to 20% and TOS IS to 7-8%."""

    elif "highest performance" in question_lower:
        state["response"] = "Your highest performance day in September was Sep 2, 2025"

    else:
        state["response"] = "I'm not sure how to answer that question. Please try rephrasing."
    
    logger.info("Returned hardcoded response")
    
    return state

