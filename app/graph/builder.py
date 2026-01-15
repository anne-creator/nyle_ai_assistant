from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.models.agentState import AgentState
from app.graph.nodes import (
    label_normalizer_node,
    message_analyzer_node,
    classify_question_node,
    metrics_query_handler_node,
    insight_query_handler_node,
    asin_product_handler_node,
    dashboard_load_handler_node,
    hardcoded_response_node,
    other_handler_node,
    goal_handler_node,
    inventory_handler_node,
    async_image_enricher_node
)


def route_by_question_type(state: AgentState) -> str:
    """Route to appropriate handler based on question type."""
    question_type = state.get("question_type", "other_query")
    
    routing_map = {
        "metrics_query": "metrics_query_handler",
        "insight_query": "insight_query_handler",
        "asin_product": "asin_product_handler",
        "dashboard_load": "dashboard_load_handler",
        "hardcoded": "hardcoded_response",
        "goal_query": "goal_handler",
        "inventory_query": "inventory_handler",
        "other_query": "other_handler"
    }
    
    return routing_map.get(question_type, "other_handler")


def create_chatbot_graph():
    """
    Build the chatbot graph with conditional routing.
    
    Flow:
    1. label_normalizer: Extracts date labels and ASIN
    2. message_analyzer: Converts labels to ISO dates (deterministic Python)
    3. classifier: Classifies question type
    4. Route to appropriate handler based on question type
    """
    
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes in order
    workflow.add_node("label_normalizer", label_normalizer_node)
    workflow.add_node("message_analyzer", message_analyzer_node)
    workflow.add_node("classifier", classify_question_node)
    
    # Add handler nodes
    workflow.add_node("metrics_query_handler", metrics_query_handler_node)
    workflow.add_node("insight_query_handler", insight_query_handler_node)
    workflow.add_node("asin_product_handler", asin_product_handler_node)
    workflow.add_node("dashboard_load_handler", dashboard_load_handler_node)
    workflow.add_node("hardcoded_response", hardcoded_response_node)
    workflow.add_node("goal_handler", goal_handler_node)
    workflow.add_node("inventory_handler", inventory_handler_node)
    workflow.add_node("other_handler", other_handler_node)
    
    # Add enrichment node
    workflow.add_node("async_image_enricher", async_image_enricher_node)
    
    # Set entry point
    workflow.set_entry_point("label_normalizer")
    
    # Chain: label_normalizer → message_analyzer → classifier
    workflow.add_edge("label_normalizer", "message_analyzer")
    workflow.add_edge("message_analyzer", "classifier")
    
    # Conditional routing after classification
    # The keys here must match what route_by_question_type RETURNS (node names)
    # When route_by_question_type returns "goal_handler", execution automatically
    # routes to the goal_handler node, which triggers goal_handler_node execution.
    workflow.add_conditional_edges(
        "classifier",
        route_by_question_type,
        {
            "metrics_query_handler": "metrics_query_handler",
            "insight_query_handler": "insight_query_handler",
            "asin_product_handler": "asin_product_handler",
            "dashboard_load_handler": "dashboard_load_handler",
            "hardcoded_response": "hardcoded_response",
            "goal_handler": "goal_handler",  # Conditional edge routes execution to goal_handler node automatically
            "inventory_handler": "inventory_handler",
            "other_handler": "other_handler"
        }
    )
    
    # ASIN handler routes to image enricher, then to END
    workflow.add_edge("asin_product_handler", "async_image_enricher")
    workflow.add_edge("async_image_enricher", END)
    
    # Other handlers end the flow directly
    workflow.add_edge("metrics_query_handler", END)
    workflow.add_edge("insight_query_handler", END)
    workflow.add_edge("dashboard_load_handler", END)
    workflow.add_edge("hardcoded_response", END)
    workflow.add_edge("goal_handler", END)
    workflow.add_edge("inventory_handler", END)
    workflow.add_edge("other_handler", END)
    
    # Add memory for conversation history
    memory = MemorySaver()
    
    return workflow.compile(checkpointer=memory)

