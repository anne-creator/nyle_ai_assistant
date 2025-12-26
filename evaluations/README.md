# LangSmith Evaluations

Evaluation infrastructure for testing individual nodes of the Nyle chatbot graph in isolation using LangSmith.

## Overview

This directory contains everything needed to run systematic, reproducible evaluations of graph nodes:
- **Dataset examples** (CSV format for LangSmith web console)
- **Node wrappers** (convert dataset inputs to graph state format)
- **Custom evaluators** (measure accuracy, validity, logic)
- **Runner scripts** (execute evaluations and log to LangSmith)

## Quick Start

### 1. Set up Environment Variables

```bash
export LANGSMITH_API_KEY="your-api-key-here"
export LANGSMITH_PROJECT="nyle-chatbot"
```

### 2. Upload Dataset to LangSmith

1. Go to https://smith.langchain.com
2. Click "Datasets" → "+ New Dataset"
3. Name: `nyle-dates-metrics-dataset`
4. Upload: `evaluations/datasets/dates_metrics_examples.csv`
5. Configure columns:
   - **Inputs**: `question`, `current_date`
   - **Outputs**: `date_start`, `date_end`

See detailed instructions: [`datasets/README.md`](datasets/README.md)

### 3. Run Evaluation

```bash
python evaluations/run_date_extraction_eval.py
```

### 4. View Results

Go to LangSmith UI → Experiments → Find your experiment

Each run includes:
- ✅ Input question and current_date
- ✅ Extracted date_start and date_end
- ✅ Expected values from dataset
- ✅ Evaluator scores (exact match, validity, logic)
- ✅ Full trace of node execution

## Directory Structure

```
evaluations/
├── __init__.py
├── README.md                          # This file
├── config.py                          # LangSmith configuration
├── node_wrappers.py                   # Convert dataset inputs to state
├── run_date_extraction_eval.py        # Main evaluation script
├── datasets/
│   ├── README.md                      # Dataset upload instructions
│   └── dates_metrics_examples.csv     # Example questions for upload
└── evaluators/
    ├── __init__.py
    └── date_accuracy.py               # Custom date extraction evaluators
```

## Current Evaluations

### extract_dates_metrics_node

**Purpose**: Test date extraction accuracy for single-period metrics queries

**Dataset**: `nyle-dates-metrics-dataset` (20 examples)

**What it tests**:
- Natural language time references ("last week", "yesterday", "Q3")
- Edge cases (month boundaries, year rollovers)
- Various date formats and phrasings

**Evaluators**:
1. **exact_date_match** - Both dates match expected exactly
2. **date_validity** - Dates are valid YYYY-MM-DD format
3. **date_logic** - date_start <= date_end
4. **date_extraction_accuracy** - Combined metric (all conditions pass)

**Runner**: `python evaluations/run_date_extraction_eval.py`

## Key Design Decisions

### Fixed Dates for Reproducibility

All examples use **fixed `current_date`** values (e.g., "2025-12-22") rather than live dates:

✅ **Benefits**:
- Tests produce same results every time
- Can test edge cases (month/year boundaries)
- CI/CD reliable (tests don't fail because a day passed)
- Version control friendly (static expected outputs)

Example:
```csv
question,current_date,date_start,date_end
"Show me last week","2025-12-22","2025-12-15","2025-12-21"
```

### Isolated Node Testing

Nodes are tested in isolation using wrappers that:
- Convert dataset inputs → graph state format
- Inject test parameters (like `current_date`)
- Don't modify main node files (all test code in `evaluations/`)

### Manual Dataset Upload

Datasets are created as CSV files and uploaded via LangSmith web console:
- No code-based dataset creation scripts
- Easy to review and edit in spreadsheet tools
- Non-technical users can contribute examples

## Adding More Evaluations

To evaluate other nodes (e.g., `extract_dates_comparison_node`):

1. **Create dataset CSV**:
   ```csv
   question,current_date,date_start,date_end,compare_date_start,compare_date_end
   "Compare this month to last month","2025-12-22","2025-12-01","2025-12-22","2025-11-01","2025-11-30"
   ```

2. **Upload to LangSmith** with appropriate name

3. **Create wrapper** in `node_wrappers.py`:
   ```python
   def create_comparison_dates_target():
       return RunnableLambda(example_to_state) | testable_comparison_node
   ```

4. **Create/reuse evaluators** in `evaluators/`

5. **Create runner script**: `run_comparison_dates_eval.py`

## Troubleshooting

### "Dataset not found"
- Verify dataset name matches exactly in LangSmith console
- Check `config.py` has correct dataset name

### "LANGSMITH_API_KEY not found"
- Set environment variable: `export LANGSMITH_API_KEY="..."`
- Or add to `.env` file

### "Module not found" errors
- Run from project root: `python evaluations/run_date_extraction_eval.py`
- Ensure virtual environment is activated

### Evaluation runs but scores are 0
- Check dataset column names match exactly
- Verify outputs structure matches what evaluators expect
- Look at individual run traces in LangSmith for details

## Resources

- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [LangSmith Evaluation Guide](https://docs.smith.langchain.com/evaluation)
- [Dataset Upload Instructions](datasets/README.md)

