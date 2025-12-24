from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.models.agentState import AgentState
from app.graph.nodes import (
    message_analyzer_node,
    classify_question_node,
    extract_dates_metrics_node,
    extract_dates_comparison_node,
    extract_dates_asin_node,
    metrics_query_handler_node,
    compare_query_handler_node,
    asin_product_handler_node,
    hardcoded_response_node,
    label_normalizer_node,
    date_calculator_node,
    extractor_evaluator_node
)


def route_by_question_type(state: AgentState) -> str:
    """Route to appropriate handler based on question type."""
    question_type = state.get("question_type", "metrics_query")
    
    routing_map = {
        "metrics_query": "metrics_query_handler",
        "compare_query": "compare_query_handler",
        "asin_product": "asin_product_handler",
        "hardcoded": "hardcoded_response"
    }
    
    return routing_map.get(question_type, "metrics_query_handler")


def create_chatbot_graph():
    """
    Build the chatbot graph with conditional routing.
    
    Flow:
    1. message_analyzer: Analyzes message, extracts date labels, ASIN, and classifies question type
    2. date_calculator: Calculates actual dates from labels
    3. Route to appropriate handler based on question type
    """
    
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add the first node: message analyzer (combines extraction + classification)
    workflow.add_node("message_analyzer", message_analyzer_node)
    
    # Add date calculator
    workflow.add_node("date_calculator", date_calculator_node)
    
    # Add handler nodes
    workflow.add_node("metrics_query_handler", metrics_query_handler_node)
    workflow.add_node("compare_query_handler", compare_query_handler_node)
    workflow.add_node("asin_product_handler", asin_product_handler_node)
    workflow.add_node("hardcoded_response", hardcoded_response_node)
    
    # Set entry point
    workflow.set_entry_point("message_analyzer")
    
    # Chain: message_analyzer → date_calculator → route to handlers
    workflow.add_edge("message_analyzer", "date_calculator")
    
    # Conditional routing after date calculation
    # The keys here must match what route_by_question_type RETURNS (node names)
    workflow.add_conditional_edges(
        "date_calculator",
        route_by_question_type,
        {
            "metrics_query_handler": "metrics_query_handler",
            "compare_query_handler": "compare_query_handler",
            "asin_product_handler": "asin_product_handler",
            "hardcoded_response": "hardcoded_response"
        }
    )
    
    # All handlers end the flow
    workflow.add_edge("metrics_query_handler", END)
    workflow.add_edge("compare_query_handler", END)
    workflow.add_edge("asin_product_handler", END)
    workflow.add_edge("hardcoded_response", END)
    
    # Add memory for conversation history
    memory = MemorySaver()
    
    return workflow.compile(checkpointer=memory)

