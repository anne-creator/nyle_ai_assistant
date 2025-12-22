from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.models.state import AgentState
from app.graph.nodes import (
    classify_question_node,
    extract_dates_metrics_node,
    extract_dates_comparison_node,
    extract_dates_asin_node,
    metrics_query_handler_node,
    compare_query_handler_node,
    asin_product_handler_node,
    hardcoded_response_node
)


def route_by_question_type(state: AgentState) -> str:
    """Route to appropriate date extraction based on question type."""
    question_type = state.get("question_type", "metrics_query")
    
    routing_map = {
        "metrics_query": "extract_dates_metrics",
        "compare_query": "extract_dates_comparison",
        "asin_product": "extract_dates_asin",
        "hardcoded": "hardcoded_response"
    }
    
    return routing_map.get(question_type, "extract_dates_metrics")


def create_chatbot_graph():
    """
    Build the chatbot graph with conditional routing.
    
    Flow:
    1. Classify question type
    2. Route to appropriate handler based on type
    3. Each handler extracts its own dates first, then processes
    """
    
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add classifier node
    workflow.add_node("classify", classify_question_node)
    
    # Add date extraction nodes (one per type)
    workflow.add_node("extract_dates_metrics", extract_dates_metrics_node)
    workflow.add_node("extract_dates_comparison", extract_dates_comparison_node)
    workflow.add_node("extract_dates_asin", extract_dates_asin_node)
    
    # Add handler nodes
    workflow.add_node("metrics_query_handler", metrics_query_handler_node)
    workflow.add_node("compare_query_handler", compare_query_handler_node)
    workflow.add_node("asin_product_handler", asin_product_handler_node)
    workflow.add_node("hardcoded_response", hardcoded_response_node)
    
    # Set entry point
    workflow.set_entry_point("classify")
    
    # Conditional routing after classification
    workflow.add_conditional_edges(
        "classify",
        route_by_question_type,
        {
            "extract_dates_metrics": "extract_dates_metrics",
            "extract_dates_comparison": "extract_dates_comparison",
            "extract_dates_asin": "extract_dates_asin",
            "hardcoded_response": "hardcoded_response"
        }
    )
    
    # Connect date extraction to handlers
    workflow.add_edge("extract_dates_metrics", "metrics_query_handler")
    workflow.add_edge("extract_dates_comparison", "compare_query_handler")
    workflow.add_edge("extract_dates_asin", "asin_product_handler")
    
    # All handlers end the flow
    workflow.add_edge("metrics_query_handler", END)
    workflow.add_edge("compare_query_handler", END)
    workflow.add_edge("asin_product_handler", END)
    workflow.add_edge("hardcoded_response", END)
    
    # Add memory for conversation history
    memory = MemorySaver()
    
    return workflow.compile(checkpointer=memory)

