# 3-Node Subgraph Evaluation

Evaluate the first 3 nodes of the pipeline together: `label_normalizer (the node1) → message_analyzer(the node 2) → extractor_evaluator(the ndoe3)`

## Files Structure

```
evaluations/subgraph_eval/
├── README.md          # This file
├── config.py          # Configuration (dataset name, experiment prefix)
├── dataset.csv        # 46 test examples (23 without ASIN + 23 with ASIN)
├── evaluators.py      # All evaluator functions
├── wrappers.py        # Subgraph builder + state conversion
└── run_eval.py        # Main runner script
```

## Evaluator Standards

### Node 1 (label_normalizer) - 7 Evaluators

| Evaluator | Criteria | Score |
|-----------|----------|-------|
| `node1_date_start_label` | Exact match of date_start_label | 1.0 or 0.0 |
| `node1_date_end_label` | Exact match of date_end_label | 1.0 or 0.0 |
| `node1_asin` | Exact match (empty string = no ASIN) | 1.0 or 0.0 |
| `node1_compare_labels` | Both compare_start and compare_end labels match | 1.0 or 0.0 |
| `node1_custom_days` | custom_days_count matches (for "past 17 days" etc.) | 1.0 or 0.0 |
| `node1_explicit_dates` | Explicit start/end dates match (YYYY-MM-DD) | 1.0 or 0.0 |
| `node1_explicit_compare_dates` | Explicit comparison dates match | 1.0 or 0.0 |

### Node 2 (message_analyzer) - 5 Evaluators

Node 2 is a **pure Python deterministic node** (no AI) that converts date labels from Node 1 into actual ISO dates.

| Evaluator | Criteria | Score |
|-----------|----------|-------|
| `node2_date_start` | Calculated date_start matches expected | 1.0 or 0.0 |
| `node2_date_end` | Calculated date_end matches expected | 1.0 or 0.0 |
| `node2_compare_dates` | Both comparison dates match | 1.0 or 0.0 |
| `node2_date_validity` | Both dates are valid YYYY-MM-DD format | 1.0 or 0.0 |
| `node2_date_logic` | date_start ≤ date_end | 1.0 or 0.0 |

### Pass-Through (metadata capture) - 3 Evaluators

| Evaluator | Criteria | Score |
|-----------|----------|-------|
| `normalizer_valid_passthrough` | Captures `_normalizer_valid` value | Always 1.0 |
| `normalizer_retries_passthrough` | Captures `_normalizer_retries` value | Always 1.0 |
| `normalizer_feedback_passthrough` | Captures `_normalizer_feedback` value | Always 1.0 |

### Combined - 1 Evaluator

| Evaluator | Criteria | Score |
|-----------|----------|-------|
| `pipeline_accuracy` | ALL Node 1 + Node 2 evaluators pass | 1.0 only if all pass |

## How to Run

### 1. Upload Dataset to LangSmith

1. Go to https://smith.langchain.com
2. Navigate to **Datasets** tab
3. Click **Create Dataset**
4. Set dataset name: `nyle-subgraph-dataset`
5. Upload file: `evaluations/subgraph_eval/dataset.csv`
6. Configure columns:
   - **Inputs**: `question`, `current_date`, `http_asin`, `http_date_start`, `http_date_end`, `sessionid`
   - **Outputs**: All `node1_*` and `node2_*` columns

### 2. Run Evaluation

```bash
# From project root
python evaluations/subgraph_eval/run_eval.py
```

### 3. View Results

1. Go to https://smith.langchain.com
2. Navigate to **Experiments** tab
3. Find experiment: `subgraph-eval-*`
4. Inspect:
   - Per-node outputs
   - Evaluator scores
   - Individual test case results
   - Full traces with LLM calls

## Dataset Examples

The dataset includes **46 examples** covering:

- **Relative dates:** today, yesterday, this week, last week
- **Year periods:** this year, last year, YTD
- **Months:** December, June, etc.
- **Past X days:** past 7 days, past 90 days, custom (past 17 days)
- **Explicit dates:** "Oct 1 to Dec 3", "Dec 1 to Oct 15"
- **Comparisons:** "today vs yesterday", "this week vs last week", "Sep to Dec"
- **With ASIN:** All above examples repeated with `B08XYZ1234`

## Configuration

Edit `config.py` to customize:

```python
DATASET_NAME = "nyle-subgraph-dataset"  # LangSmith dataset name
EXPERIMENT_PREFIX = "subgraph-eval"      # Experiment name prefix
MAX_CONCURRENCY = 4                      # Parallel evaluation threads
```

## Troubleshooting

**Error: LANGSMITH_API_KEY not found**
- Set environment variable: `export LANGSMITH_API_KEY='your-key-here'`
- Or add to `.env.local` file

**Error: Dataset not found**
- Verify dataset name matches `DATASET_NAME` in `config.py`
- Ensure dataset is uploaded to LangSmith web console

**Error: Column mismatch**
- Verify dataset has all required input/output columns
- Check column names match exactly (case-sensitive)

