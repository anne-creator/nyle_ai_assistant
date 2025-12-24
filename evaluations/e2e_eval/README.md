# End-to-End Graph Evaluation

This is an end-to-end test that evaluates the complete graph execution without using HTTP calls. The graph runs entirely in-process, making it suitable for testing without hosting servers locally.

## Overview

Unlike HTTP-based end-to-end tests that require running servers, this evaluation:
- Runs the complete graph directly in the test process
- Does not make any HTTP calls to external services
- Tests the full pipeline from user question to final answer
- Evaluates graph behavior, node execution, and response generation

## Files Structure

```
evaluations/e2e_eval/
├── README.md          # This file
├── config.py          # Configuration (dataset name, experiment prefix)
├── dataset.csv        # Test dataset (empty - add your test cases)
├── evaluators.py      # Evaluator functions
├── wrappers.py        # Graph wrapper for evaluation
└── run_eval.py        # Main runner script
```

## Evaluators

### Response Completeness
- **Criteria**: Response exists and is not an error message
- **Score**: 1.0 if valid response, 0.0 otherwise

### Graph Execution Success
- **Criteria**: Graph completed without errors
- **Score**: 1.0 if no errors, 0.0 if errors occurred

### Final Answer Presence
- **Criteria**: Final answer exists in output
- **Score**: 1.0 if present, 0.0 if missing

### Nodes Executed
- **Criteria**: Expected nodes were executed
- **Score**: 1.0 if all expected nodes ran, 0.5 if some ran, 0.0 if none

### Pipeline Success
- **Criteria**: Combined check of all success indicators
- **Score**: 1.0 if all checks pass, 0.0 otherwise

## How to Run

### 1. Prepare Dataset

Add test cases to `dataset.csv` with the following columns:
- `question`: User's question
- `current_date`: Current date (YYYY-MM-DD format)
- `http_asin`: Product ASIN (optional)
- `http_date_start`: Date range start (optional)
- `http_date_end`: Date range end (optional)
- `sessionid`: Session identifier

Example:
```csv
question,current_date,http_asin,http_date_end,http_date_start,sessionid
"what is today's ROI","2025-12-24","","","","session-001"
"show me metrics for B08XYZ1234","2025-12-24","B08XYZ1234","","","session-002"
```

### 2. Upload Dataset to LangSmith

1. Go to https://smith.langchain.com
2. Navigate to **Datasets** tab
3. Click **Create Dataset**
4. Set dataset name: `nyle-e2e-dataset`
5. Upload file: `evaluations/e2e_eval/dataset.csv`
6. Configure columns:
   - **Inputs**: `question`, `current_date`, `http_asin`, `http_date_start`, `http_date_end`, `sessionid`

### 3. Run Evaluation

```bash
# From project root
python evaluations/e2e_eval/run_eval.py
```

### 4. View Results

1. Go to https://smith.langchain.com
2. Navigate to **Experiments** tab
3. Find experiment: `e2e-eval-*`
4. Inspect:
   - Response completeness
   - Graph execution success
   - Node execution tracking
   - Full pipeline traces

## Configuration

Edit `config.py` to customize:

```python
DATASET_NAME = "nyle-e2e-dataset"  # LangSmith dataset name
EXPERIMENT_PREFIX = "e2e-eval"      # Experiment name prefix
MAX_CONCURRENCY = 4                 # Parallel evaluation threads
```

## Key Differences from HTTP Tests

| Aspect | E2E (This Test) | HTTP Tests |
|--------|-----------------|------------|
| **Server Required** | No | Yes |
| **Network Calls** | None | Required |
| **Test Speed** | Fast | Slower |
| **Setup Complexity** | Low | High |
| **What It Tests** | Graph logic & flow | Full API integration |

## Troubleshooting

**Error: LANGSMITH_API_KEY not found**
- Set environment variable: `export LANGSMITH_API_KEY='your-key-here'`
- Or add to `.env.local` file

**Error: Dataset not found**
- Verify dataset name matches `DATASET_NAME` in `config.py`
- Ensure dataset is uploaded to LangSmith web console

**Error: Column mismatch**
- Verify dataset has all required input columns
- Check column names match exactly (case-sensitive)

**Error: Graph execution failed**
- Check all app dependencies are installed
- Verify `.env.local` has required configuration
- Ensure database connections are available (if needed)

## Adding Test Cases

To add new test cases:
1. Edit `dataset.csv`
2. Add a new row with test data
3. Re-upload to LangSmith (or create new dataset version)
4. Run evaluation again

## Notes

- This test does not require local servers to be running
- All graph execution happens in-process
- No HTTP calls are made during evaluation
- Ideal for testing graph logic and node behavior
- Does not test HTTP API endpoints or server integration

