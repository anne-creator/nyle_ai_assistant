"""
Evaluator functions for end-to-end evaluation.

All evaluators follow LangSmith standards:
- Accept (run, example) parameters
- Return dict with 'key' and 'score' (float 0.0-1.0)
"""


def response_completeness(run, example):
    """
    Check if the response is complete (not empty or error).
    
    Score:
    - 1.0: Response exists and is not an error message
    - 0.0: Response is empty or contains error
    """
    output = run.outputs or {}
    response = output.get("response", "")
    
    if not response:
        return {"key": "response_completeness", "score": 0.0}
    
    error_indicators = ["error", "failed", "exception", "unable to"]
    has_error = any(indicator in response.lower() for indicator in error_indicators)
    
    return {
        "key": "response_completeness",
        "score": 0.0 if has_error else 1.0
    }


def graph_execution_success(run, example):
    """
    Check if the graph executed successfully without errors.
    
    Score:
    - 1.0: Graph completed successfully
    - 0.0: Graph execution failed
    """
    output = run.outputs or {}
    error = output.get("error")
    
    return {
        "key": "graph_execution_success",
        "score": 0.0 if error else 1.0
    }


def final_answer_presence(run, example):
    """
    Check if final answer exists in the output.
    
    Score:
    - 1.0: Final answer is present
    - 0.0: Final answer is missing
    """
    output = run.outputs or {}
    final_answer = output.get("final_answer")
    
    return {
        "key": "final_answer_presence",
        "score": 1.0 if final_answer else 0.0
    }


def nodes_executed(run, example):
    """
    Check if expected nodes were executed in the graph.
    
    Score:
    - 1.0: All expected nodes executed
    - 0.5: Some nodes executed
    - 0.0: No nodes executed
    """
    output = run.outputs or {}
    nodes = output.get("nodes_executed", [])
    
    if not nodes:
        return {"key": "nodes_executed", "score": 0.0}
    
    # Check if common nodes were executed
    expected_nodes = ["label_normalizer", "message_analyzer"]
    executed_expected = sum(1 for node in expected_nodes if node in nodes)
    
    if executed_expected == len(expected_nodes):
        score = 1.0
    elif executed_expected > 0:
        score = 0.5
    else:
        score = 0.0
    
    return {
        "key": "nodes_executed",
        "score": score
    }


def pipeline_success(run, example):
    """
    Combined evaluator: checks overall pipeline success.
    
    Score:
    - 1.0: All components successful
    - 0.0: Any component failed
    """
    output = run.outputs or {}
    
    # Check multiple success indicators
    has_response = bool(output.get("response"))
    no_error = not output.get("error")
    has_final_answer = bool(output.get("final_answer"))
    
    all_success = has_response and no_error and has_final_answer
    
    return {
        "key": "pipeline_success",
        "score": 1.0 if all_success else 0.0
    }

