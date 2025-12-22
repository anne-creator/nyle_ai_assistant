"""
Node wrappers for LangSmith evaluation.

These wrappers convert LangSmith dataset inputs into graph state format
and provide test-friendly versions of nodes that accept injected parameters.
"""
from typing import Dict, Any
from unittest.mock import patch
from datetime import datetime
from langchain_core.runnables import RunnableLambda

from app.models.state import AgentState
from app.graph.nodes.extract_dates_metrics.node import extract_dates_metrics_node


def example_to_state(inputs: Dict[str, Any]) -> AgentState:
    """
    Convert LangSmith dataset inputs into AgentState format.
    
    Args:
        inputs: Dictionary from LangSmith dataset with keys:
            - question: str (the user's question)
            - current_date: str (YYYY-MM-DD format, fixed for reproducibility)
    
    Returns:
        AgentState with minimal required fields for extract_dates_metrics_node
    """
    return {
        "messages": [],
        "question": inputs["question"],
        "question_type": "metrics_query",
        # Store current_date in state so we can inject it during execution
        "_test_current_date": inputs["current_date"]
    }


def create_testable_extract_dates_node():
    """
    Create a test-friendly wrapper around extract_dates_metrics_node
    that injects the current_date from state instead of using datetime.now().
    
    This allows reproducible testing without modifying the main node file.
    
    Returns:
        RunnableLambda that wraps the node with date injection
    """
    def wrapped_node(state: AgentState) -> AgentState:
        # Get the test current_date from state (injected by example_to_state)
        test_date = state.get("_test_current_date")
        
        if test_date:
            # Mock datetime.now() to return the fixed test date
            mock_datetime = datetime.strptime(test_date, "%Y-%m-%d")
            with patch('app.graph.nodes.extract_dates_metrics.node.datetime') as mock_dt:
                mock_dt.now.return_value = mock_datetime
                mock_dt.strftime = datetime.strftime
                result = extract_dates_metrics_node(state)
        else:
            # If no test date, run normally (for production)
            result = extract_dates_metrics_node(state)
        
        # Clean up test metadata from result
        if "_test_current_date" in result:
            result = {k: v for k, v in result.items() if k != "_test_current_date"}
        
        return result
    
    return RunnableLambda(wrapped_node)


def create_dates_metrics_target():
    """
    Create the full evaluation target: example_to_state | testable_node
    
    This is what gets passed to LangSmith's evaluate/aevaluate function.
    
    Returns:
        Runnable chain that takes LangSmith inputs and outputs AgentState
    """
    return RunnableLambda(example_to_state) | create_testable_extract_dates_node()

