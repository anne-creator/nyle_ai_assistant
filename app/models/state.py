from typing import TypedDict, List, Optional, Literal
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """State passed through the LangGraph execution."""
    
    # Core conversation
    messages: List[BaseMessage]
    question: str
    
    # PRIMARY date parameters (always present after extraction)
    date_start: str
    date_end: str
    
    # COMPARISON date parameters (for compare_query type)
    compare_date_start: Optional[str]
    compare_date_end: Optional[str]
    
    # ASIN parameter (for asin_product type)
    asin: Optional[str]
    
    # Question routing
    question_type: Literal[
        "metrics_query",      # Single period metric questions
        "compare_query",      # Two period comparisons
        "asin_product",       # ASIN-specific questions
        "hardcoded"           # Hardcoded responses
    ]
    
    # Metrics processing
    requested_metrics: Optional[List[str]]
    metric_data: Optional[dict]
    comparison_metric_data: Optional[dict]
    
    # Final output
    response: str

