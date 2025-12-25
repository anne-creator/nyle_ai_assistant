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
    hardcoded_response_node,
    other_handler_node
)


def route_by_question_type(state: AgentState) -> str:
    """Route to appropriate handler based on question type."""
    question_type = state.get("question_type", "other")
    
    routing_map = {
        "metrics_query": "metrics_query_handler",
        "compare_query": "compare_query_handler",
        "asin_product": "asin_product_handler",
        "hardcoded": "hardcoded_response",
        "other": "other_handler"
    }
    
    return routing_map.get(question_type, "other_handler")


def route_after_evaluation(state: AgentState) -> str:
    """
    Route after Node 3 evaluation.
    
    Returns:
        - "classifier": If extraction is valid OR max retries reached (continue pipeline)
        - "label_normalizer": If extraction is invalid AND retries < 3 (retry loop)
    """
    is_valid = state.get("_normalizer_valid", False)
    retries = state.get("_normalizer_retries", 0)
    
    # Continue forward if valid OR max retries exceeded
    if is_valid or retries >= 3:
        return "classifier"
    else:
        # Retry: go back to label_normalizer
        return "label_normalizer"


def create_chatbot_graph():
    """
    Build the chatbot graph with conditional routing.
    
    Flow:
    1. label_normalizer: Extracts date labels and ASIN (supports retry with feedback)
    2. message_analyzer: Converts labels to ISO dates (deterministic Python)
    3. extractor_evaluator: AI-powered validation with feedback generation
    4. [CONDITIONAL] If invalid and retries < 3: loop back to label_normalizer
    5. [CONDITIONAL] If valid or retries >= 3: continue to classifier
    6. classifier: Classifies question type
    7. Route to appropriate handler based on question type
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
    workflow.add_node("other_handler", other_handler_node)
    
    # Set entry point
    workflow.set_entry_point("label_normalizer")
    
    # Chain: label_normalizer → message_analyzer → extractor_evaluator
    workflow.add_edge("label_normalizer", "message_analyzer")
    workflow.add_edge("message_analyzer", "extractor_evaluator")
    
    # Conditional routing after evaluation: retry loop or continue
    workflow.add_conditional_edges(
        "extractor_evaluator",
        route_after_evaluation,
        {
            "classifier": "classifier",
            "label_normalizer": "label_normalizer"  # Retry loop
        }
    )
    
    # Conditional routing after classification
    # The keys here must match what route_by_question_type RETURNS (node names)
    workflow.add_conditional_edges(
        "classifier",
        route_by_question_type,
        {
            "metrics_query_handler": "metrics_query_handler",
            "compare_query_handler": "compare_query_handler",
            "asin_product_handler": "asin_product_handler",
            "hardcoded_response": "hardcoded_response",
            "other_handler": "other_handler"
        }
    )
    
    # All handlers end the flow
    workflow.add_edge("metrics_query_handler", END)
    workflow.add_edge("compare_query_handler", END)
    workflow.add_edge("asin_product_handler", END)
    workflow.add_edge("hardcoded_response", END)
    workflow.add_edge("other_handler", END)
    
    # Add memory for conversation history
    memory = MemorySaver()
    
    return workflow.compile(checkpointer=memory)

