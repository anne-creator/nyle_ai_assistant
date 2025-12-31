"""
Custom evaluators for the 3-node subgraph evaluation.

Evaluator Standards:
====================

NODE 1 (label_normalizer) - Label Extraction Accuracy:
- node1_date_start_label: Exact match of extracted start date label
- node1_date_end_label: Exact match of extracted end date label  
- node1_asin: Exact match of extracted ASIN (empty string == no ASIN)
- node1_compare_labels: Exact match of comparison date labels (for compare queries)
- node1_custom_days: Exact match of custom_days_count (for "past X days" queries)
- node1_explicit_dates: Exact match of explicit dates (for specific date queries)
- node1_explicit_compare_dates: Exact match of explicit comparison dates

NODE 2 (date_calculator) - Date Calculation Accuracy:
- node2_date_start: Exact match of calculated start date (YYYY-MM-DD)
- node2_date_end: Exact match of calculated end date (YYYY-MM-DD)
- node2_compare_dates: Exact match of calculated comparison dates
- node2_date_validity: Dates are valid YYYY-MM-DD format
- node2_date_logic: date_start <= date_end (logical order)

PASS-THROUGH (metadata capture, always score 1.0):
- normalizer_valid: Captures _normalizer_valid value
- normalizer_retries: Captures _normalizer_retries value
- normalizer_feedback: Captures _normalizer_feedback value

COMBINED:
- pipeline_accuracy: 1.0 only if ALL core evaluators pass
"""
from datetime import datetime
from typing import Dict, Any
from langsmith.schemas import Run, Example


# ============================================================
# NODE 1 EVALUATORS (label_normalizer)
# ============================================================

def node1_date_start_label(run: Run, example: Example) -> Dict[str, Any]:
    """
    Check if Node 1 extracted the correct date_start_label.
    
    Score: 1.0 if exact match, 0.0 otherwise
    """
    extracted = run.outputs.get("_date_start_label") or ""
    expected = example.outputs.get("node1_date_start_label") or ""
    
    is_correct = extracted == expected
    return {
        "key": "node1_date_start_label",
        "score": 1.0 if is_correct else 0.0,
        "comment": f"Extracted: {extracted} | Expected: {expected}"
    }


def node1_date_end_label(run: Run, example: Example) -> Dict[str, Any]:
    """
    Check if Node 1 extracted the correct date_end_label.
    
    Score: 1.0 if exact match, 0.0 otherwise
    """
    extracted = run.outputs.get("_date_end_label") or ""
    expected = example.outputs.get("node1_date_end_label") or ""
    
    is_correct = extracted == expected
    return {
        "key": "node1_date_end_label",
        "score": 1.0 if is_correct else 0.0,
        "comment": f"Extracted: {extracted} | Expected: {expected}"
    }


def node1_asin(run: Run, example: Example) -> Dict[str, Any]:
    """
    Check if Node 1 extracted the correct ASIN.
    
    Score: 1.0 if exact match (including both empty), 0.0 otherwise
    """
    extracted = run.outputs.get("asin") or ""
    expected = example.outputs.get("node1_asin") or ""
    
    is_correct = extracted == expected
    return {
        "key": "node1_asin",
        "score": 1.0 if is_correct else 0.0,
        "comment": f"Extracted: {extracted} | Expected: {expected}"
    }


def node1_compare_labels(run: Run, example: Example) -> Dict[str, Any]:
    """
    Check if Node 1 extracted correct comparison date labels.
    
    Score: 1.0 if both start and end labels match, 0.0 otherwise
    """
    extracted_start = run.outputs.get("_compare_date_start_label") or ""
    extracted_end = run.outputs.get("_compare_date_end_label") or ""
    expected_start = example.outputs.get("node1_compare_date_start_label") or ""
    expected_end = example.outputs.get("node1_compare_date_end_label") or ""
    
    is_correct = (extracted_start == expected_start and extracted_end == expected_end)
    return {
        "key": "node1_compare_labels",
        "score": 1.0 if is_correct else 0.0,
        "comment": f"Extracted: ({extracted_start}, {extracted_end}) | Expected: ({expected_start}, {expected_end})"
    }


def node1_custom_days(run: Run, example: Example) -> Dict[str, Any]:
    """
    Check if Node 1 extracted correct custom_days_count.
    
    Score: 1.0 if match (None/empty both mean no custom days), 0.0 otherwise
    """
    extracted = run.outputs.get("_custom_days_count")
    expected = example.outputs.get("node1_custom_days_count")
    
    # Normalize: empty string or None both mean no custom days
    try:
        extracted_val = int(extracted) if extracted else None
    except (ValueError, TypeError):
        extracted_val = None
    
    try:
        expected_val = int(expected) if expected else None
    except (ValueError, TypeError):
        expected_val = None
    
    is_correct = extracted_val == expected_val
    return {
        "key": "node1_custom_days",
        "score": 1.0 if is_correct else 0.0,
        "comment": f"Extracted: {extracted_val} | Expected: {expected_val}"
    }


def node1_explicit_dates(run: Run, example: Example) -> Dict[str, Any]:
    """
    Check if Node 1 extracted correct explicit dates.
    
    Score: 1.0 if both dates match, 0.0 otherwise
    """
    extracted_start = run.outputs.get("_explicit_date_start") or ""
    extracted_end = run.outputs.get("_explicit_date_end") or ""
    expected_start = example.outputs.get("node1_explicit_date_start") or ""
    expected_end = example.outputs.get("node1_explicit_date_end") or ""
    
    is_correct = (extracted_start == expected_start and extracted_end == expected_end)
    return {
        "key": "node1_explicit_dates",
        "score": 1.0 if is_correct else 0.0,
        "comment": f"Extracted: ({extracted_start}, {extracted_end}) | Expected: ({expected_start}, {expected_end})"
    }


def node1_explicit_compare_dates(run: Run, example: Example) -> Dict[str, Any]:
    """
    Check if Node 1 extracted correct explicit comparison dates.
    
    Score: 1.0 if both dates match, 0.0 otherwise
    """
    extracted_start = run.outputs.get("_explicit_compare_start") or ""
    extracted_end = run.outputs.get("_explicit_compare_end") or ""
    expected_start = example.outputs.get("node1_explicit_compare_start") or ""
    expected_end = example.outputs.get("node1_explicit_compare_end") or ""
    
    is_correct = (extracted_start == expected_start and extracted_end == expected_end)
    return {
        "key": "node1_explicit_compare_dates",
        "score": 1.0 if is_correct else 0.0,
        "comment": f"Extracted: ({extracted_start}, {extracted_end}) | Expected: ({expected_start}, {expected_end})"
    }


# ============================================================
# NODE 2 EVALUATORS (date_calculator)
# ============================================================

def node2_date_start(run: Run, example: Example) -> Dict[str, Any]:
    """
    Check if calculated date_start is correct.
    
    Score: 1.0 if exact match, 0.0 otherwise
    """
    extracted = run.outputs.get("date_start") or ""
    expected = example.outputs.get("node2_date_start") or ""
    
    is_correct = extracted == expected
    return {
        "key": "node2_date_start",
        "score": 1.0 if is_correct else 0.0,
        "comment": f"Calculated: {extracted} | Expected: {expected}"
    }


def node2_date_end(run: Run, example: Example) -> Dict[str, Any]:
    """
    Check if calculated date_end is correct.
    
    Score: 1.0 if exact match, 0.0 otherwise
    """
    extracted = run.outputs.get("date_end") or ""
    expected = example.outputs.get("node2_date_end") or ""
    
    is_correct = extracted == expected
    return {
        "key": "node2_date_end",
        "score": 1.0 if is_correct else 0.0,
        "comment": f"Calculated: {extracted} | Expected: {expected}"
    }


def node2_compare_dates(run: Run, example: Example) -> Dict[str, Any]:
    """
    Check if calculated comparison dates are correct.
    
    Score: 1.0 if both dates match, 0.0 otherwise
    """
    extracted_start = run.outputs.get("compare_date_start") or ""
    extracted_end = run.outputs.get("compare_date_end") or ""
    expected_start = example.outputs.get("node2_compare_date_start") or ""
    expected_end = example.outputs.get("node2_compare_date_end") or ""
    
    is_correct = (extracted_start == expected_start and extracted_end == expected_end)
    return {
        "key": "node2_compare_dates",
        "score": 1.0 if is_correct else 0.0,
        "comment": f"Calculated: ({extracted_start}, {extracted_end}) | Expected: ({expected_start}, {expected_end})"
    }


def node2_date_validity(run: Run, example: Example) -> Dict[str, Any]:
    """
    Verify calculated dates are valid YYYY-MM-DD format.
    
    Score: 1.0 if both dates are valid format, 0.0 otherwise
    """
    date_start = run.outputs.get("date_start", "")
    date_end = run.outputs.get("date_end", "")
    
    def is_valid_date(date_str: str) -> bool:
        if not date_str:
            return False
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except (ValueError, TypeError):
            return False
    
    both_valid = is_valid_date(date_start) and is_valid_date(date_end)
    return {
        "key": "node2_date_validity",
        "score": 1.0 if both_valid else 0.0,
        "comment": f"start={date_start}, end={date_end}"
    }


def node2_date_logic(run: Run, example: Example) -> Dict[str, Any]:
    """
    Ensure date_start <= date_end (logical order).
    
    Score: 1.0 if start <= end, 0.0 otherwise
    """
    date_start = run.outputs.get("date_start", "")
    date_end = run.outputs.get("date_end", "")
    
    try:
        start_dt = datetime.strptime(date_start, "%Y-%m-%d")
        end_dt = datetime.strptime(date_end, "%Y-%m-%d")
        is_logical = start_dt <= end_dt
    except (ValueError, TypeError):
        is_logical = False
    
    return {
        "key": "node2_date_logic",
        "score": 1.0 if is_logical else 0.0,
        "comment": f"{date_start} <= {date_end}: {is_logical}"
    }


# ============================================================
# PASS-THROUGH EVALUATORS (always score 1.0)
# Captures normalizer metadata without affecting results
# ============================================================

def normalizer_valid_passthrough(run: Run, example: Example) -> Dict[str, Any]:
    """
    Pass-through evaluator for _normalizer_valid.
    
    Always scores 1.0 - captures value for visibility only.
    """
    value = run.outputs.get("_normalizer_valid")
    return {
        "key": "normalizer_valid",
        "score": 1.0,
        "comment": f"Value: {value}"
    }


def normalizer_retries_passthrough(run: Run, example: Example) -> Dict[str, Any]:
    """
    Pass-through evaluator for _normalizer_retries.
    
    Always scores 1.0 - captures value for visibility only.
    """
    value = run.outputs.get("_normalizer_retries")
    return {
        "key": "normalizer_retries",
        "score": 1.0,
        "comment": f"Value: {value}"
    }


def normalizer_feedback_passthrough(run: Run, example: Example) -> Dict[str, Any]:
    """
    Pass-through evaluator for _normalizer_feedback.
    
    Always scores 1.0 - captures value for visibility only.
    """
    value = run.outputs.get("_normalizer_feedback")
    return {
        "key": "normalizer_feedback",
        "score": 1.0,
        "comment": f"Value: {value}"
    }


# ============================================================
# COMBINED EVALUATORS
# ============================================================

def pipeline_accuracy(run: Run, example: Example) -> Dict[str, Any]:
    """
    Overall pipeline accuracy - ALL core evaluators must pass.
    
    Checks:
    - Node 1: date labels + ASIN + comparison labels
    - Node 2: calculated dates + validity + logic
    
    Score: 1.0 if ALL pass, 0.0 otherwise
    """
    # Node 1 checks
    n1_start = node1_date_start_label(run, example)
    n1_end = node1_date_end_label(run, example)
    n1_asin_result = node1_asin(run, example)
    n1_compare = node1_compare_labels(run, example)
    
    # Node 2 checks
    n2_start = node2_date_start(run, example)
    n2_end = node2_date_end(run, example)
    n2_compare = node2_compare_dates(run, example)
    n2_valid = node2_date_validity(run, example)
    n2_logic = node2_date_logic(run, example)
    
    all_pass = (
        n1_start["score"] == 1.0 and
        n1_end["score"] == 1.0 and
        n1_asin_result["score"] == 1.0 and
        n1_compare["score"] == 1.0 and
        n2_start["score"] == 1.0 and
        n2_end["score"] == 1.0 and
        n2_compare["score"] == 1.0 and
        n2_valid["score"] == 1.0 and
        n2_logic["score"] == 1.0
    )
    
    failed = []
    if n1_start["score"] != 1.0: failed.append("n1_start_label")
    if n1_end["score"] != 1.0: failed.append("n1_end_label")
    if n1_asin_result["score"] != 1.0: failed.append("n1_asin")
    if n1_compare["score"] != 1.0: failed.append("n1_compare")
    if n2_start["score"] != 1.0: failed.append("n2_date_start")
    if n2_end["score"] != 1.0: failed.append("n2_date_end")
    if n2_compare["score"] != 1.0: failed.append("n2_compare")
    if n2_valid["score"] != 1.0: failed.append("n2_validity")
    if n2_logic["score"] != 1.0: failed.append("n2_logic")
    
    return {
        "key": "pipeline_accuracy",
        "score": 1.0 if all_pass else 0.0,
        "comment": f"Failed: {failed}" if failed else "All passed"
    }



