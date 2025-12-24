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
    
    question_lower = state["question"].lower()
    
    if "performance insight" in question_lower or "performance compare" in question_lower:
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

