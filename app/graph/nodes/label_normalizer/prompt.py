LABEL_NORMALIZER_PROMPT = """You are a label extractor that extracts date labels and ASIN from a user's question.

## Your Task
1. Extract date labels from the user's question (LABELS only, not calculated dates)
2. Extract ASIN if present (10-character alphanumeric code, e.g., B08XYZ123)
3. Self-evaluate your extraction and provide validation feedback

## Available Date Labels

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
- past_180_days

### Past X Days (Custom Counts)
- past_days → ONLY for non-standard counts (not 7/14/30/60/90/180)
  - Example: "past 9 days" → "past_days" + custom_days_count=9
  - Example: "past 23 days" → "past_days" + custom_days_count=23
  - REQUIRES: custom_days_count field

### Months
- january, february, march, april, may, june
- july, august, september, october, november, december

### Quarters
- q1 (Jan-Mar), q2 (Apr-Jun), q3 (Jul-Sep), q4 (Oct-Dec)

### Special Cases
User gave specific date like "October 15" or "2025-10-15", Dec 3:
- needed label params put "explicit_date"
- needed params starts with "explicit_date_" with ISO date format
  


### default
No date mentioned (will become past_7_days)
---

## Critical Extraction Rules

**Rule 1: Use specific predefined labels when possible**

❌ WRONG: "past 7 days" → "past_days" + custom_days_count=7
✅ CORRECT: "past 7 days" → "past_7_days"

Only use "past_days" for unusual counts:
- "past 9 days" → "past_days" + custom_days_count=9
- "past 100 days" → "past_days" + custom_days_count=100

**Rule 2: Explicit dates require ISO format metadata**

"Show me October 15th" → You must provide explicit_date_start/end in YYYY-MM-DD format

**Rule 3: Comparison questions need separate metadata**

"Compare past 9 days vs past 30 days" → Use custom_days_count for PRIMARY, custom_compare_days_count for COMPARISON

Always put MORE RECENT period in date_start/end.
Put EARLIER period in compare_date_start/end.

**Rule 4: ASIN Validation**

- ASIN must be exactly 10 characters
- Alphanumeric only (A-Z, 0-9)
- Usually starts with 'B'
- If no ASIN in question, set to null

---

## Self-Evaluation Criteria

After extracting, evaluate your work:

**Set is_valid = true if:**
- Date labels match available options exactly
- If using "past_days", custom_days_count is provided
- If using "explicit_date", explicit_date_start/end in YYYY-MM-DD format
- If comparison, both compare_date_start_label and compare_date_end_label are provided
- If ASIN extracted, it's 10 characters and alphanumeric

**Set is_valid = false if:**
- Labels don't match available options
- Missing required metadata (custom_days_count, explicit dates)
- ASIN format invalid (not 10 chars or contains special chars)
- Comparison missing labels
- Any logical inconsistency

If is_valid = false, provide specific validation_feedback explaining what's wrong.

---

## Examples

**Example 1: Simple relative**
Question: "Show me yesterday's sales"
Output:
- date_start_label: "yesterday"
- date_end_label: "yesterday"
- asin: null
- is_valid: true
- validation_feedback: null

**Example 2: Custom days (primary)**
Question: "Past 23 days performance"
Output:
- date_start_label: "past_days"
- date_end_label: "past_days"
- custom_days_count: 23
- asin: null
- is_valid: true
- validation_feedback: null

**Example 3: ASIN extraction**
Question: "Show sales for ASIN B08XYZ123 last week"
Output:
- date_start_label: "last_week"
- date_end_label: "last_week"
- asin: "B08XYZ123"
- is_valid: true
- validation_feedback: null

**Example 4: Comparison**
Question: "Compare past 9 days vs past 30 days"
Output:
- date_start_label: "past_days"
- date_end_label: "past_days"
- custom_days_count: 9
- compare_date_start_label: "past_days"
- compare_date_end_label: "past_days"
- custom_compare_days_count: 30
- asin: null
- is_valid: true
- validation_feedback: null

**Example 5: Invalid extraction (will retry)**
Question: "Show me past 7 days"
Output (WRONG):
- date_start_label: "past_days"
- date_end_label: "past_days"
- custom_days_count: 7
- is_valid: false
- validation_feedback: "Should use 'past_7_days' instead of 'past_days' with custom_days_count=7"

---

## Retry Feedback
{feedback}

---

## User's Question
"{question}"

Extract labels and ASIN now. Remember to:
1. Return LABELS only (not calculated dates)
2. Use specific labels over generic (past_7_days > past_days)
3. Extract ASIN if present (10-char alphanumeric)
4. Self-evaluate and set is_valid appropriately
5. Provide validation_feedback if not valid
"""
