# LABEL_NORMALIZER_PROMPT
# Fill this prompt template as needed

LABEL_NORMALIZER_PROMPT = """
LABEL_EXTRACTOR_PROMPT = \"\"\"You are a label extractor that extract date labels from a user's question.

## Your Task
- analyze the user's question and extract the date labels that are most relevant to the question.
Extract date labels from the user's question. Return LABELS only (not calculated dates).

## Available Labels

### Relative Time
- today, yesterday
- this_week, last_week
- this_month, last_month
- this_year, last_year
- ytd (year to date)

### Past X Days (Predefined Counts)
- past_7_days
- past_14_days
- past_30_days
- past_60_days
- past_90_days
_ past_180_days

### Past X Days (Custom Counts)
- past_days → ONLY for non-standard counts (not 7/14/30/60/90)
  - Example: "past 9 days" → "past_days" + custom_days_count=9
  - Example: "past 23 days" → "past_days" + custom_days_count=23
  - REQUIRES: custom_days_count field

### Months
- january, february, march, april, may, june
- july, august, september, october, november, december

### Quarters
- q1 (Jan-Mar), q2 (Apr-Jun), q3 (Jul-Sep), q4 (Oct-Dec)

### Special Cases
- explicit_date → User gave specific date like "October 15" or "2025-10-15"
  - REQUIRES: explicit_date_start/end in YYYY-MM-DD format
- default → 


### default
No date mentioned (will become past_7_days)
---

## Critical Rules

**Rule 1: Use specific predefined labels when possible**

❌ WRONG:
"past 7 days" → "past_days" + custom_days_count=7

✅ CORRECT:
"past 7 days" → "past_7_days"

Only use "past_days" for unusual counts:
- "past 9 days" → "past_days" + custom_days_count=9
- "past 100 days" → "past_days" + custom_days_count=100

**Rule 2: Explicit dates require ISO format metadata**

"Show me October 15th" →
```json
{
  "date_start_label": "explicit_date",
  "date_end_label": "explicit_date",
  "explicit_date_start": "2025-10-15",
  "explicit_date_end": "2025-10-15"
}
```

You must convert natural dates to YYYY-MM-DD format.

**Rule 3: Comparison questions need separate metadata**

"Compare past 9 days vs past 30 days" →
```json
{
  "date_start_label": "past_days",
  "date_end_label": "past_days",
  "custom_days_count": 9,
  "compare_date_start_label": "past_days",
  "compare_date_end_label": "past_days",
  "custom_compare_days_count": 30
}
```

Notice: custom_days_count for PRIMARY, custom_compare_days_count for COMPARISON.

Always put MORE RECENT period in date_start/end.
Put EARLIER period in compare_date_start/end.

**Rule 4: Same label, different counts**

"Compare past 9 days vs past 23 days" →
```json
{
  "date_start_label": "past_days",
  "custom_days_count": 9,
  "compare_date_start_label": "past_days",
  "custom_compare_days_count": 23
}
```

Both use "past_days" but different metadata fields!

---

## Full Examples

**Example 1: Simple relative**
```
Question: "Show me yesterday's sales"
Output: {
  "date_start_label": "yesterday",
  "date_end_label": "yesterday"
}
```

**Example 2: Custom days (primary)**
```
Question: "Past 23 days performance"
Output: {
  "date_start_label": "past_days",
  "date_end_label": "past_days",
  "custom_days_count": 23
}
```

**Example 3: Explicit date**
```
Question: "October 15th data"
Output: {
  "date_start_label": "explicit_date",
  "date_end_label": "explicit_date",
  "explicit_date_start": "2025-10-15",
  "explicit_date_end": "2025-10-15"
}
```

**Example 4: Date range**
```
Question: "From Oct 1 to Dec 15"
Output: {
  "date_start_label": "explicit_date",
  "date_end_label": "explicit_date",
  "explicit_date_start": "2025-10-01",
  "explicit_date_end": "2025-12-15"
}
```

**Example 5: Comparison with same label type**
```
Question: "Compare past 9 days vs past 30 days"
Output: {
  "date_start_label": "past_days",
  "date_end_label": "past_days",
  "custom_days_count": 9,
  "compare_date_start_label": "past_days",
  "compare_date_end_label": "past_days",
  "custom_compare_days_count": 30
}
```

**Example 6: Comparison with different labels**
```
Question: "Compare this month vs last month"
Output: {
  "date_start_label": "this_month",
  "date_end_label": "this_month",
  "compare_date_start_label": "last_month",
  "compare_date_end_label": "last_month"
}
```

**Example 7: Mixed comparison**
```
Question: "Compare yesterday vs past 7 days"
Output: {
  "date_start_label": "yesterday",
  "date_end_label": "yesterday",
  "compare_date_start_label": "past_7_days",
  "compare_date_end_label": "past_7_days"
}
```

---

## Retry Feedback
{feedback}

---

## User's Question
"{question}"

Extract labels now. Remember:
- Return LABELS only (not calculated dates)
- Use specific labels over generic (past_7_days > past_days)
- Separate metadata: custom_days_count vs custom_compare_days_count
- User message dates override HTTP dates
\"\"\"
"""

