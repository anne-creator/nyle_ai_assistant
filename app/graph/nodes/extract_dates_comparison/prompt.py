EXTRACT_DATES_COMPARISON_PROMPT = """Extract TWO date ranges for comparison. Today is {current_date}.

The question asks to compare two periods. Extract:
- date_start/date_end = MORE RECENT period
- compare_date_start/compare_date_end = EARLIER period

Examples:
- "Compare August vs September" →
  date_start: 2025-09-01, date_end: 2025-09-30 (September)
  compare_date_start: 2025-08-01, compare_date_end: 2025-08-31 (August)

- "How did sales change from last month to this month?" →
  date_start: 2025-12-01, date_end: 2025-12-20 (this month)
  compare_date_start: 2025-11-01, compare_date_end: 2025-11-30 (last month)

Question: {question}

Return JSON with all 4 date fields (YYYY-MM-DD)."""

