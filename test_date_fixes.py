#!/usr/bin/env python3
"""Quick test script to verify date extraction fixes."""

from datetime import date
from app.graph.nodes.extract_dates_metrics.date_utils import (
    try_pattern_matching,
    calculate_last_x_days
)

# Test date: December 22, 2025
test_date = date(2025, 12, 22)

# Critical test cases from the analysis
test_cases = [
    # Issue #1: Last X Days
    ("Last 7 days attribution_sales", "2025-12-16", "2025-12-22"),
    ("Show me ROI for last 3 days", "2025-12-20", "2025-12-22"),
    ("Get organic_impressions from last 5 days", "2025-12-18", "2025-12-22"),
    ("Show me safety_stock for the last 10 days", "2025-12-13", "2025-12-22"),
    ("Last 21 days total_sales", "2025-12-02", "2025-12-22"),
    ("Show me ROI for last 30 days", "2025-11-23", "2025-12-22"),
    ("Get organic_impressions for the last 45 days", "2025-11-08", "2025-12-22"),
    ("Last 90 days safety_stock performance", "2025-09-24", "2025-12-22"),
    ("Show me ad_sales for last 120 days", "2025-08-25", "2025-12-22"),
    ("Past 180 days total_sales data", "2025-06-26", "2025-12-22"),
    
    # Issue #2: Default 7-day range
    ("Show me ROI", "2025-12-16", "2025-12-22"),
    ("Show me ad_sales", "2025-12-16", "2025-12-22"),
    ("Show me organic_impressions", "2025-12-16", "2025-12-22"),
    ("What is my stores overall performance", "2025-12-16", "2025-12-22"),
    
    # Issue #3: Today queries
    ("Show me ROI for today", "2025-12-22", "2025-12-22"),
    ("Show me organic_impressions today", "2025-12-22", "2025-12-22"),
    ("What's the attribution_sales for today", "2025-12-22", "2025-12-22"),
    ("Show me today's safety_stock", "2025-12-22", "2025-12-22"),
    ("Get ad_sales for today", "2025-12-22", "2025-12-22"),
    
    # Issue #4: Month names
    ("January total_sales", "2025-01-01", "2025-01-31"),
    ("Show me ROI for September", "2025-09-01", "2025-09-30"),
    ("Get October organic_impressions", "2025-10-01", "2025-10-31"),
    
    # Issue #5: Past X days
    ("Past 14 days ad_sales", "2025-12-09", "2025-12-22"),
    ("Past 60 days attribution_sales", "2025-10-24", "2025-12-22"),
    
    # Yesterday (should already work)
    ("Show me the total ctr for yesterday", "2025-12-21", "2025-12-21"),
    ("Get yesterday's organic_impressions", "2025-12-21", "2025-12-21"),
]

print("=" * 70)
print("DATE EXTRACTION FIX VERIFICATION")
print("=" * 70)
print(f"Test Date: {test_date.strftime('%Y-%m-%d')}")
print()

passed = 0
failed = 0
failed_cases = []

for question, expected_start, expected_end in test_cases:
    result = try_pattern_matching(question, test_date)
    
    if result:
        actual_start, actual_end = result
        if actual_start == expected_start and actual_end == expected_end:
            passed += 1
            status = "✅ PASS"
        else:
            failed += 1
            status = f"❌ FAIL: Got {actual_start} to {actual_end}"
            failed_cases.append((question, expected_start, expected_end, actual_start, actual_end))
    else:
        failed += 1
        status = "❌ FAIL: No pattern matched (would use LLM)"
        failed_cases.append((question, expected_start, expected_end, "None", "None"))
    
    print(f"{status}")
    print(f"  Q: {question}")
    print(f"  Expected: {expected_start} to {expected_end}")
    if result:
        print(f"  Actual:   {result[0]} to {result[1]}")
    print()

print("=" * 70)
print(f"RESULTS: {passed}/{len(test_cases)} passed ({passed/len(test_cases)*100:.1f}%)")
print("=" * 70)

if failed_cases:
    print("\n❌ FAILED CASES:")
    for question, exp_start, exp_end, act_start, act_end in failed_cases:
        print(f"  • {question}")
        print(f"    Expected: {exp_start} to {exp_end}")
        print(f"    Got:      {act_start} to {act_end}")
        print()

# Test the calculation function directly
print("\n" + "=" * 70)
print("CALCULATION VERIFICATION")
print("=" * 70)
calc_tests = [
    (1, ("2025-12-22", "2025-12-22")),
    (3, ("2025-12-20", "2025-12-22")),
    (7, ("2025-12-16", "2025-12-22")),
    (30, ("2025-11-23", "2025-12-22")),
    (90, ("2025-09-24", "2025-12-22")),
]

for days, expected in calc_tests:
    result = calculate_last_x_days(test_date, days)
    status = "✅" if result == expected else "❌"
    print(f"{status} Last {days} days: {result} (expected {expected})")

