"""
Custom evaluators for date extraction accuracy.

These evaluators inspect LangSmith Run objects and compare outputs
against expected values from the dataset.
"""
from datetime import datetime
from typing import Dict, Any
from langsmith.schemas import Run, Example


def exact_date_match(run: Run, example: Example) -> Dict[str, Any]:
    """
    Check if extracted dates exactly match expected dates.
    
    Returns:
        Dict with score 1.0 if both dates match, 0.0 otherwise
    """
    # Get extracted outputs from the node
    extracted_start = run.outputs.get("date_start")
    extracted_end = run.outputs.get("date_end")
    
    # Get expected outputs from dataset
    expected_start = example.outputs.get("date_start")
    expected_end = example.outputs.get("date_end")
    
    # Check if both match
    is_correct = (
        extracted_start == expected_start and 
        extracted_end == expected_end
    )
    
    return {
        "key": "exact_date_match",
        "score": 1.0 if is_correct else 0.0
    }


def date_validity_check(run: Run, example: Example) -> Dict[str, Any]:
    """
    Verify that extracted dates are in valid YYYY-MM-DD format.
    
    Returns:
        Dict with score 1.0 if dates are valid format, 0.0 otherwise
    """
    extracted_start = run.outputs.get("date_start", "")
    extracted_end = run.outputs.get("date_end", "")
    
    def is_valid_date(date_str: str) -> bool:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except (ValueError, TypeError):
            return False
    
    both_valid = is_valid_date(extracted_start) and is_valid_date(extracted_end)
    
    return {
        "key": "date_validity",
        "score": 1.0 if both_valid else 0.0
    }


def date_logic_check(run: Run, example: Example) -> Dict[str, Any]:
    """
    Ensure date_start <= date_end (logical consistency).
    
    Returns:
        Dict with score 1.0 if logic is correct, 0.0 otherwise
    """
    extracted_start = run.outputs.get("date_start", "")
    extracted_end = run.outputs.get("date_end", "")
    
    try:
        start_dt = datetime.strptime(extracted_start, "%Y-%m-%d")
        end_dt = datetime.strptime(extracted_end, "%Y-%m-%d")
        is_logical = start_dt <= end_dt
    except (ValueError, TypeError):
        # If dates are invalid format, fail this check
        is_logical = False
    
    return {
        "key": "date_logic",
        "score": 1.0 if is_logical else 0.0
    }


def date_extraction_accuracy(run: Run, example: Example) -> Dict[str, Any]:
    """
    Combined accuracy metric: checks validity, logic, and correctness.
    
    Only scores 1.0 if ALL conditions are met:
    - Dates are valid YYYY-MM-DD format
    - date_start <= date_end
    - Both dates exactly match expected values
    
    Returns:
        Dict with score 1.0 if perfect, 0.0 otherwise
    """
    validity = date_validity_check(run, example)
    logic = date_logic_check(run, example)
    exactness = exact_date_match(run, example)
    
    all_pass = (
        validity["score"] == 1.0 and 
        logic["score"] == 1.0 and 
        exactness["score"] == 1.0
    )
    
    return {
        "key": "date_extraction_accuracy",
        "score": 1.0 if all_pass else 0.0
    }

