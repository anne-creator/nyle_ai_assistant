EXTRACT_DATES_ASIN_PROMPT = """Extract ASIN and date range. Today is {current_date}.

Extract:
1. ASIN - The product identifier (format: B0XXXXXXXXX)
2. Date range - Same rules as metrics queries

Date rules:
- "yesterday" → {current_date} minus 1 day
- "last week" → 7 days ago to yesterday
- "past month" → 30 days ago to today
- No time reference → 7 days ago to today (default)

Question: {question}

Return JSON with asin, date_start, and date_end."""

