import re
from datetime import datetime, timedelta, date
from typing import Optional, Tuple
import calendar


def extract_today(question: str) -> bool:
    """Check if question asks for today's data."""
    patterns = [
        r'\btoday\b',
        r'\btoday\'s\b',
        r'\btodays\b',
        r'\bfor today\b',
    ]
    question_lower = question.lower()
    return any(re.search(pattern, question_lower) for pattern in patterns)


def extract_yesterday(question: str) -> bool:
    """Check if question asks for yesterday's data."""
    patterns = [
        r'\byesterday\b',
        r'\byesterday\'s\b',
        r'\byesterdays\b',
    ]
    question_lower = question.lower()
    return any(re.search(pattern, question_lower) for pattern in patterns)


def extract_last_x_days(question: str) -> Optional[int]:
    """Extract number of days from 'last X days' or 'past X days' pattern."""
    patterns = [
        r'\blast\s+(\d+)\s+days?\b',
        r'\bpast\s+(\d+)\s+days?\b',
    ]
    question_lower = question.lower()
    
    for pattern in patterns:
        match = re.search(pattern, question_lower)
        if match:
            return int(match.group(1))
    
    return None


def extract_month_name(question: str) -> Optional[int]:
    """Extract month number from month name in question."""
    month_map = {
        'january': 1, 'jan': 1,
        'february': 2, 'feb': 2,
        'march': 3, 'mar': 3,
        'april': 4, 'apr': 4,
        'may': 5,
        'june': 6, 'jun': 6,
        'july': 7, 'jul': 7,
        'august': 8, 'aug': 8,
        'september': 9, 'sep': 9, 'sept': 9,
        'october': 10, 'oct': 10,
        'november': 11, 'nov': 11,
        'december': 12, 'dec': 12,
    }
    
    question_lower = question.lower()
    
    # Build pattern from month names
    month_pattern = r'\b(' + '|'.join(month_map.keys()) + r')\b'
    match = re.search(month_pattern, question_lower)
    
    if match:
        month_name = match.group(1)
        return month_map[month_name]
    
    return None


def has_explicit_date_reference(question: str) -> bool:
    """Check if question contains explicit dates like 'Oct 1', '10/1', '2025-10-01'."""
    patterns = [
        r'\d{4}-\d{2}-\d{2}',  # 2025-10-01
        r'\d{1,2}/\d{1,2}(/\d{2,4})?',  # 10/1 or 10/1/2025
        r'\b\d{1,2}(st|nd|rd|th)?\b',  # 1st, 2nd, 15, etc.
        r'\b(from|to|through|between)\b',  # Date range keywords
    ]
    
    question_lower = question.lower()
    return any(re.search(pattern, question_lower) for pattern in patterns)


def calculate_today(current_date: date) -> Tuple[str, str]:
    """Calculate date range for 'today' query."""
    date_str = current_date.strftime("%Y-%m-%d")
    return date_str, date_str


def calculate_yesterday(current_date: date) -> Tuple[str, str]:
    """Calculate date range for 'yesterday' query."""
    yesterday = current_date - timedelta(days=1)
    date_str = yesterday.strftime("%Y-%m-%d")
    return date_str, date_str


def calculate_last_x_days(current_date: date, num_days: int) -> Tuple[str, str]:
    """
    Calculate date range for 'last X days' query.
    
    'Last X days' includes today, so we go back X-1 days.
    Example: 'last 7 days' on Dec 22 = Dec 16 to Dec 22 (7 days total)
    """
    days_to_subtract = num_days - 1
    start_date = current_date - timedelta(days=days_to_subtract)
    return start_date.strftime("%Y-%m-%d"), current_date.strftime("%Y-%m-%d")


def calculate_month_range(current_date: date, month_num: int) -> Tuple[str, str]:
    """Calculate full month date range."""
    year = current_date.year
    
    # Get last day of month
    last_day = calendar.monthrange(year, month_num)[1]
    
    start_date = date(year, month_num, 1)
    end_date = date(year, month_num, last_day)
    
    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


def calculate_default_range(current_date: date) -> Tuple[str, str]:
    """Calculate default 7-day range when no date is specified."""
    return calculate_last_x_days(current_date, 7)


def try_pattern_matching(question: str, current_date: date) -> Optional[Tuple[str, str]]:
    """
    Try to extract dates using pattern matching.
    Returns (date_start, date_end) if pattern matched, None otherwise.
    """
    # Priority 1: Check for 'today'
    if extract_today(question):
        return calculate_today(current_date)
    
    # Priority 2: Check for 'yesterday'
    if extract_yesterday(question):
        return calculate_yesterday(current_date)
    
    # Priority 3: Check for 'last X days' or 'past X days'
    num_days = extract_last_x_days(question)
    if num_days is not None:
        return calculate_last_x_days(current_date, num_days)
    
    # Priority 4: Check for month name (only if no explicit dates)
    if not has_explicit_date_reference(question):
        month_num = extract_month_name(question)
        if month_num is not None:
            return calculate_month_range(current_date, month_num)
    
    # Priority 5: Check if no date reference at all (default to 7 days)
    if not has_explicit_date_reference(question) and not extract_month_name(question):
        return calculate_default_range(current_date)
    
    # No pattern matched - has explicit dates, let LLM handle it
    return None

