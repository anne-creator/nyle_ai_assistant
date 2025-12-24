"""
Subgraph wrappers for evaluating the first 3 nodes together.

Creates a linear subgraph: label_normalizer -> message_analyzer -> extractor_evaluator -> date_calculator
Each node's output is captured for LangSmith visibility.
"""
import sys
from pathlib import Path
from typing import TypedDict, Optional, List, Literal, Annotated, Dict, Any
from datetime import datetime
from unittest.mock import patch

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from langchain_core.runnables import RunnableLambda

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.models.date_labels import DateLabelLiteral
from app.graph.nodes.label_normalizer.node import label_normalizer_node
from app.graph.nodes.message_analyzer.node import message_analyzer_node
from app.graph.nodes.extractor_evaluator.node import extractor_evaluator_node
from app.graph.nodes.date_calculator.node import date_calculator_node


class SubgraphState(TypedDict):
    """
    State for 3-node subgraph evaluation.
    
    Includes all fields needed by the nodes and dedicated output keys
    for per-node inspection in LangSmith.
    """
    # ========== Input ==========
    messages: Annotated[List[BaseMessage], add_messages]
    question: str
    
    # ========== Test Metadata ==========
    _test_current_date: Optional[str]
    
    # ========== HTTP Request Params (from dataset) ==========
    _http_date_start: Optional[str]
    _http_date_end: Optional[str]
    _http_asin: Optional[str]
    
    # ========== Node 1 Outputs (label_normalizer) ==========
    _date_start_label: Optional[DateLabelLiteral]
    _date_end_label: Optional[DateLabelLiteral]
    _compare_date_start_label: Optional[DateLabelLiteral]
    _compare_date_end_label: Optional[DateLabelLiteral]
    _explicit_date_start: Optional[str]
    _explicit_date_end: Optional[str]
    _explicit_compare_start: Optional[str]
    _explicit_compare_end: Optional[str]
    _custom_days_count: Optional[int]
    _custom_compare_days_count: Optional[int]
    asin: Optional[str]
    
    # Normalizer self-evaluation metadata
    _normalizer_valid: Optional[bool]
    _normalizer_retries: Optional[int]
    _normalizer_feedback: Optional[str]
    
    # ========== Node 2/3 Outputs (after date_calculator) ==========
    date_start: Optional[str]
    date_end: Optional[str]
    compare_date_start: Optional[str]
    compare_date_end: Optional[str]
    
    # ========== Question Type (set by classifier or message_analyzer) ==========
    question_type: Optional[Literal["metrics_query", "compare_query", "asin_product", "hardcoded"]]


def example_to_subgraph_state(inputs: Dict[str, Any]) -> SubgraphState:
    """
    Convert LangSmith dataset inputs into SubgraphState format.
    
    Args:
        inputs: Dictionary from LangSmith dataset with keys:
            - question: str
            - current_date: str (YYYY-MM-DD)
            - http_asin, http_date_start, http_date_end: optional HTTP params
            - sessionid: session identifier
    
    Returns:
        SubgraphState initialized for evaluation
    """
    return {
        "messages": [],
        "question": inputs["question"],
        "_test_current_date": inputs.get("current_date"),
        "_http_date_start": inputs.get("http_date_start") or None,
        "_http_date_end": inputs.get("http_date_end") or None,
        "_http_asin": inputs.get("http_asin") or None,
    }


def node1_wrapped(state: SubgraphState) -> SubgraphState:
    """
    Wrapper for label_normalizer_node.
    
    Runs the actual node and returns updated state.
    """
    result = label_normalizer_node(state)
    return result


def node2_wrapped(state: SubgraphState) -> SubgraphState:
    """
    Wrapper for message_analyzer_node.
    
    Note: In current graph, message_analyzer is a pass-through node.
    """
    result = message_analyzer_node(state)
    return result


def node3_wrapped(state: SubgraphState) -> SubgraphState:
    """
    Wrapper for extractor_evaluator_node.
    
    Note: In current graph, extractor_evaluator is a pass-through node.
    """
    result = extractor_evaluator_node(state)
    return result


def date_calculator_wrapped(state: SubgraphState) -> SubgraphState:
    """
    Wrapper for date_calculator_node that injects test current_date.
    
    This allows reproducible testing by mocking datetime.now().
    """
    test_date = state.get("_test_current_date")
    
    if test_date:
        # Parse the test date
        mock_date = datetime.strptime(test_date, "%Y-%m-%d").date()
        
        # Mock the DateCalculator to use our test date
        with patch('app.utils.date_calculator.datetime') as mock_dt:
            # Configure mock
            mock_dt.now.return_value.date.return_value = mock_date
            mock_dt.strptime = datetime.strptime
            
            # Also patch timezone-aware now
            from datetime import timezone
            mock_dt.now.return_value = datetime.combine(mock_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            
            result = date_calculator_node(state)
    else:
        result = date_calculator_node(state)
    
    return result


def create_three_node_subgraph():
    """
    Create evaluation subgraph: label_normalizer -> message_analyzer -> extractor_evaluator -> date_calculator.
    
    This tests the first 3 extraction nodes plus date calculation.
    
    Returns:
        Compiled StateGraph for evaluation
    """
    workflow = StateGraph(SubgraphState)
    
    # Add nodes
    workflow.add_node("label_normalizer", node1_wrapped)
    workflow.add_node("message_analyzer", node2_wrapped)
    workflow.add_node("extractor_evaluator", node3_wrapped)
    workflow.add_node("date_calculator", date_calculator_wrapped)
    
    # Wire edges
    workflow.add_edge(START, "label_normalizer")
    workflow.add_edge("label_normalizer", "message_analyzer")
    workflow.add_edge("message_analyzer", "extractor_evaluator")
    workflow.add_edge("extractor_evaluator", "date_calculator")
    workflow.add_edge("date_calculator", END)
    
    return workflow.compile()


def create_subgraph_target():
    """
    Create the full evaluation target for LangSmith.
    
    Pipeline: example_to_state -> 3-node subgraph -> date_calculator
    
    Returns:
        Runnable chain for aevaluate()
    """
    subgraph = create_three_node_subgraph()
    return RunnableLambda(example_to_subgraph_state) | subgraph

