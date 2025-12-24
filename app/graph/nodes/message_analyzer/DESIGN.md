# Message Analyzer Node - First Node Design

## Overview
The `message_analyzer` node is the **FIRST NODE** in the chatbot graph. It performs comprehensive analysis of the user's message and extracts all critical information needed for downstream processing.

## What It Does

### 1. Date Label Extraction
Analyzes the user message and extracts **4 date label fields**:

- `_date_start_label` - Primary period start
- `_date_end_label` - Primary period end
- `_compare_date_start_label` - Comparison period start (optional)
- `_compare_date_end_label` - Comparison period end (optional)

**Valid labels** (from `date_labels.py`):
- Relative: `today`, `yesterday`, `this_week`, `last_week`, `this_month`, `last_month`, `this_year`, `last_year`, `ytd`
- Past days: `past_7_days`, `past_14_days`, `past_30_days`, `past_60_days`, `past_90_days`, `past_180_days`
- Custom days: `past_days` (requires `custom_days_count`)
- Months: `january`, `february`, ..., `december`
- Special: `explicit_date` (requires explicit date metadata), `default`

### 2. ASIN Extraction
Detects and validates Amazon ASINs in the message:

- **Format**: 10-character alphanumeric code (e.g., `B08XYZ123`, `B0B5HN65QQ`)
- **Validation**: Uses regex pattern matching + format validation
- **Fallback**: Extracts from raw text if LLM misses it

### 3. Question Type Classification
Classifies the question into one of 4 types for routing:

- `metrics_query` - Store-level metrics (ACOS, sales, profit)
- `compare_query` - Comparing two time periods
- `asin_product` - Questions about a specific product/ASIN
- `hardcoded` - Special questions with pre-defined responses

### 4. Flow Re-evaluation
After extraction, the node **re-evaluates** the classification:
- If ASIN is found and type is `metrics_query` → change to `asin_product`
- This ensures accurate routing based on extracted data

## Structured Output

Uses Pydantic `MessageAnalysis` model with strict typing:

```python
class MessageAnalysis(BaseModel):
    # Date labels
    date_start_label: DateLabelLiteral
    date_end_label: DateLabelLiteral
    compare_date_start_label: Optional[DateLabelLiteral]
    compare_date_end_label: Optional[DateLabelLiteral]
    
    # Metadata for explicit dates
    explicit_date_start: Optional[str]
    explicit_date_end: Optional[str]
    explicit_compare_start: Optional[str]
    explicit_compare_end: Optional[str]
    
    # Metadata for custom days
    custom_days_count: Optional[int]
    
    # ASIN
    asin: Optional[str]
    
    # Classification
    question_type: Literal["metrics_query", "compare_query", "asin_product", "hardcoded"]
```

## Examples

### Example 1: Simple Metrics Query
```
Input: "What was my ACOS yesterday?"

Output:
- date_start_label: "yesterday"
- date_end_label: "yesterday"
- compare_date_start_label: null
- compare_date_end_label: null
- asin: null
- question_type: "metrics_query"
```

### Example 2: ASIN Product Query
```
Input: "Show sales for ASIN B08XYZ123 last week"

Output:
- date_start_label: "last_week"
- date_end_label: "last_week"
- compare_date_start_label: null
- compare_date_end_label: null
- asin: "B08XYZ123"
- question_type: "asin_product"
```

### Example 3: Comparison Query
```
Input: "Compare August vs September sales"

Output:
- date_start_label: "september"
- date_end_label: "september"
- compare_date_start_label: "august"
- compare_date_end_label: "august"
- asin: null
- question_type: "compare_query"
```

### Example 4: Custom Days
```
Input: "Show me past 23 days performance"

Output:
- date_start_label: "past_days"
- date_end_label: "past_days"
- custom_days_count: 23
- asin: null
- question_type: "metrics_query"
```

### Example 5: Explicit Dates
```
Input: "What were sales from Oct 1 to Dec 15?"

Output:
- date_start_label: "explicit_date"
- date_end_label: "explicit_date"
- explicit_date_start: "2025-10-01"
- explicit_date_end: "2025-12-15"
- asin: null
- question_type: "metrics_query"
```

### Example 6: Complex Comparison with ASIN
```
Input: "Compare past 9 days vs past 30 days for ASIN B0B5HN65QQ"

Output:
- date_start_label: "past_days"
- date_end_label: "past_days"
- custom_days_count: 9
- compare_date_start_label: "past_30_days"
- compare_date_end_label: "past_30_days"
- asin: "B0B5HN65QQ"
- question_type: "compare_query"
```

## State Updates

The node updates the following AgentState fields:

### Date Labels
- `_date_start_label`
- `_date_end_label`
- `_compare_date_start_label`
- `_compare_date_end_label`

### Date Metadata
- `_explicit_date_start`
- `_explicit_date_end`
- `_explicit_compare_start`
- `_explicit_compare_end`
- `_custom_days_count`

### ASIN & Classification
- `asin`
- `question_type`

## Error Handling

If extraction fails:
- Falls back to safe defaults: `default` label (past 7 days)
- Sets ASIN to `None`
- Sets question_type to `"metrics_query"`
- Logs error for debugging

## Integration with Graph

### New Simplified Flow
```
1. message_analyzer (THIS NODE)
   ↓
2. date_calculator (converts labels to ISO dates)
   ↓
3. Route to handler based on question_type:
   - metrics_query → metrics_query_handler
   - compare_query → compare_query_handler
   - asin_product → asin_product_handler
   - hardcoded → hardcoded_response
```

### Removed Nodes
The new design **replaces** these old nodes:
- ❌ `label_normalizer` (now part of message_analyzer)
- ❌ `classifier` (now part of message_analyzer)
- ❌ `extractor_evaluator` (no longer needed)
- ❌ `extract_dates_metrics` (dates calculated earlier)
- ❌ `extract_dates_comparison` (dates calculated earlier)
- ❌ `extract_dates_asin` (dates calculated earlier)

## Benefits

1. **Single Source of Truth**: All extraction happens in one place
2. **Type Safety**: Uses `DateLabelLiteral` for compile-time validation
3. **ASIN Detection**: Robust regex-based extraction with validation
4. **Flow Re-evaluation**: Smart classification based on extracted data
5. **Cleaner Architecture**: Reduced from 6+ nodes to 2 nodes before handlers
6. **Better Maintainability**: Single prompt, single node to update
7. **Comprehensive Logging**: Clear visibility into extraction process

