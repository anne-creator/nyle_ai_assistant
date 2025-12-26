# app/models/state.py

from typing import TypedDict, List, Optional, Literal, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from app.models.date_labels import DateLabelLiteral


class AgentState(TypedDict):
    """
    State passed through the LangGraph execution.
    
    All date label fields use DateLabelLiteral for type safety.
    This prevents typos and enforces valid values.
    """
    
    # ========== Core Conversation ==========
    messages: Annotated[List[BaseMessage], add_messages]
    question: str
    
    # ========== HTTP Request Original Params: initialized in main.py for each message ==========
    _http_date_start: Optional[str]      # Can be any string from frontend
    _http_date_end: Optional[str]        # Can be any string from frontend
    _http_compare_date_start: Optional[str]  # Can be any string from frontend
    _http_compare_date_end: Optional[str]    # Can be any string from frontend
    _http_asin: Optional[str]            # Can be any string from frontend
    
    # ========== Node 1 Outputs: Extracted Labels ==========
    # ⚡ TYPE SAFE: These can ONLY be valid DateLabelLiteral values
    _date_start_label: Optional[DateLabelLiteral]
    _date_end_label: Optional[DateLabelLiteral]
    _compare_date_start_label: Optional[DateLabelLiteral]
    _compare_date_end_label: Optional[DateLabelLiteral]
    
    # ========== Node 1 Outputs: Label Metadata ==========
    # For EXPLICIT_DATE label - can be any ISO date string
    _explicit_date_start: Optional[str]
    _explicit_date_end: Optional[str]
    _explicit_compare_start: Optional[str]
    _explicit_compare_end: Optional[str]
    
    # For PAST_DAYS label - must be positive integer
    _custom_days_count: Optional[int]
    _custom_compare_days_count: Optional[int]
    
    # ========== Node 2 Outputs: Calculated Dates ==========
    # These are ISO format strings (YYYY-MM-DD)
    date_start: str
    date_end: str
    compare_date_start: Optional[str]
    compare_date_end: Optional[str]
    
    # ========== ASIN ==========
    asin: Optional[str]  # B0XXXXXXXXX format
    
    # ========== Node 3 Outputs: Evaluation ==========
    _normalizer_valid: Optional[bool]
    _normalizer_retries: Optional[int]
    _normalizer_feedback: Optional[str]
    
    # ========== Classifier Output ==========
    question_type: Literal[
        "metrics_query",
        "compare_query",
        "asin_product",
        "hardcoded",
        "other_query"
    ]
    
    # ========== Handler Processing ==========
    requested_metrics: Optional[List[str]]
    metric_data: Optional[dict]
    comparison_metric_data: Optional[dict]
    
    # ========== Final Output ==========
    response: str