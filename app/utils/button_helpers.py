"""
Button markup helper utilities.

This module provides functions to generate button markup strings
for various user interactions in the chat interface.
"""

import json


def create_set_goal_button(
    metric_name: str, 
    metric_value: float, 
    date_start: str, 
    date_end: str
) -> str:
    """
    Generate set_goal button markup.
    
    Args:
        metric_name: Name of the metric (e.g., "acos", "total_sales", "roi")
        metric_value: Current value of the metric
        date_start: Start date (YYYY-MM-DD)
        date_end: End date (YYYY-MM-DD)
    
    Returns:
        Button markup string in format: [BUTTON:set_goal:{payload}:Setup Optimal Goal]
    
    Example:
        >>> create_set_goal_button("acos", 25.5, "2024-01-01", "2024-01-31")
        '[BUTTON:set_goal:{"acos":25.5,"date_start":"2024-01-01","date_end":"2024-01-31"}:Setup Optimal Goal]'
    """
    payload = {
        metric_name: metric_value,
        "date_start": date_start,
        "date_end": date_end
    }
    
    # Compact JSON - no spaces
    payload_str = json.dumps(payload, separators=(',', ':'))
    
    return f"[BUTTON:set_goal:{payload_str}:Setup Optimal Goal]"
