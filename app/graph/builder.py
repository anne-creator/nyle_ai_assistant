from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.models.agentState import AgentState
from app.graph.nodes import (
    label_normalizer_node,
    message_analyzer_node,
    extractor_evaluator_node,
    classify_question_node,
    metrics_query_handler_node,
    compare_query_handler_node,
    asin_product_handler_node,
    hardcoded_response_node
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
    1. label_normalizer: Extracts date labels and ASIN (with self-evaluation and retry)
    2. message_analyzer: Pass-through node (does nothing)
    3. extractor_evaluator: Pass-through node (does nothing)
    4. classifier: Classifies question type
    5. Route to appropriate handler based on question type
    """
    
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes in order
    workflow.add_node("label_normalizer", label_normalizer_node)
    workflow.add_node("message_analyzer", message_analyzer_node)
    workflow.add_node("extractor_evaluator", extractor_evaluator_node)
    workflow.add_node("classifier", classify_question_node)
    
    # Add handler nodes
    workflow.add_node("metrics_query_handler", metrics_query_handler_node)
    workflow.add_node("compare_query_handler", compare_query_handler_node)
    workflow.add_node("asin_product_handler", asin_product_handler_node)
    workflow.add_node("hardcoded_response", hardcoded_response_node)
    
    # Set entry point
    workflow.set_entry_point("label_normalizer")
    
    # Chain: label_normalizer → message_analyzer → extractor_evaluator → classifier → route to handlers
    workflow.add_edge("label_normalizer", "message_analyzer")
    workflow.add_edge("message_analyzer", "extractor_evaluator")
    workflow.add_edge("extractor_evaluator", "classifier")
    
    # Conditional routing after classification
    # The keys here must match what route_by_question_type RETURNS (node names)
    workflow.add_conditional_edges(
        "classifier",
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

