EXTRACT_DATES_METRICS_PROMPT = """Extract date range for metrics query. Today is {current_date}.

Rules:
- "yesterday" → {current_date} minus 1 day
- "last week" → 7 days ago to yesterday
- "past month" → 30 days ago to today
- "this month" → first day of month to today
- "August" → 2025-08-01 to 2025-08-31
- No time reference → 7 days ago to today (default)

Question: {question}

Return JSON with date_start and date_end (YYYY-MM-DD)."""

