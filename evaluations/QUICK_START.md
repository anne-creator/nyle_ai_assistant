# Quick Start Guide: LangSmith Evaluation

## Step 1: Upload Dataset to LangSmith Web Console

### Dataset File
**Location**: `evaluations/datasets/dates_metrics_examples.csv`

### Upload Instructions

1. **Go to LangSmith**: https://smith.langchain.com
2. **Navigate**: Click "Datasets" in left sidebar
3. **Create**: Click "+ New Dataset"
4. **Name**: Enter `nyle-dates-metrics-dataset`
5. **Description**: "Date extraction evaluation for metrics queries with fixed current_date"
6. **Upload**: Click "Upload CSV" and select `dates_metrics_examples.csv`
7. **Configure Columns**:
   - **Input columns**: Select `question` and `current_date`
   - **Output columns**: Select `date_start` and `date_end`
8. **Create**: Click "Create Dataset"

### CSV Format Reference

The CSV has exactly 4 columns:

```csv
question,current_date,date_start,date_end
"Show me last week's sales","2025-12-22","2025-12-15","2025-12-21"
"What was yesterday's performance?","2025-12-22","2025-12-21","2025-12-21"
```

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `question` | Input | User's natural language query | "Show me last week's sales" |
| `current_date` | Input | Fixed reference date (YYYY-MM-DD) | "2025-12-22" |
| `date_start` | Output | Expected start date (YYYY-MM-DD) | "2025-12-15" |
| `date_end` | Output | Expected end date (YYYY-MM-DD) | "2025-12-21" |

### Why Fixed `current_date`?

Using fixed dates ensures:
- ✅ **Reproducibility**: Same inputs always produce same expected outputs
- ✅ **Edge case testing**: Can test month/year boundaries, leap years
- ✅ **CI/CD reliability**: Tests don't fail just because a day passed
- ✅ **Version control**: Static expected outputs can be tracked in git

## Step 2: Set Environment Variables

```bash
export LANGSMITH_API_KEY="your-langsmith-api-key"
export LANGSMITH_PROJECT="nyle-chatbot"
```

Get your API key from: https://smith.langchain.com/settings

## Step 3: Run Evaluation

From project root:

```bash
python evaluations/run_date_extraction_eval.py
```

Expected output:
```
============================================================
LangSmith Evaluation: extract_dates_metrics_node
============================================================
🔍 Validating configuration...
✅ LangSmith project: nyle-chatbot
✅ Dataset: nyle-dates-metrics-dataset

🔧 Creating evaluation target...
✅ Node target created: example_to_state | extract_dates_metrics_node
✅ Loaded 4 evaluators

🚀 Starting evaluation...
   Dataset: nyle-dates-metrics-dataset
   Concurrency: 4
   Experiment prefix: dates-metrics-eval

This may take a few minutes...

✅ Evaluation complete!
```

## Step 4: View Results in LangSmith

1. Go to https://smith.langchain.com
2. Click "Experiments" in left sidebar
3. Find experiment with prefix: `dates-metrics-eval`
4. Click to open and view:
   - 📊 Overall accuracy metrics
   - 📝 Individual test cases (passed/failed)
   - 🔍 Full traces with inputs/outputs
   - 📈 Evaluator scores per example

### What You'll See

For each example:
- **Input**: Question + current_date
- **Output**: Extracted date_start and date_end
- **Expected**: Ground truth from dataset
- **Scores**:
  - `exact_date_match`: 1.0 if both dates match exactly
  - `date_validity`: 1.0 if dates are valid YYYY-MM-DD format
  - `date_logic`: 1.0 if date_start <= date_end
  - `date_extraction_accuracy`: 1.0 if all above pass

## Troubleshooting

### Error: "Dataset nyle-dates-metrics-dataset not found"

**Solution**: 
1. Check dataset name in LangSmith console matches exactly
2. Verify dataset was created successfully
3. Check you're in the correct LangSmith project

### Error: "LANGSMITH_API_KEY not found"

**Solution**:
```bash
export LANGSMITH_API_KEY="your-key-here"
```

### Evaluation runs but all scores are 0

**Solution**:
1. Check column names in LangSmith match CSV exactly
2. Verify input columns: `question`, `current_date`
3. Verify output columns: `date_start`, `date_end`
4. Look at individual run traces in LangSmith for details

### Import errors

**Solution**:
```bash
# Make sure you're in project root
cd /Users/anne/Document/project/Nyle/Nyle_chatbot

# Activate virtual environment
source venv/bin/activate

# Run evaluation
python evaluations/run_date_extraction_eval.py
```

## Next Steps

### Add More Test Cases

1. Edit `evaluations/datasets/dates_metrics_examples.csv`
2. Add more rows with diverse questions
3. Re-upload to LangSmith (updates existing dataset)
4. Re-run evaluation

### Test Other Nodes

Follow the pattern in [`evaluations/README.md`](README.md) to create evaluations for:
- `extract_dates_comparison_node`
- `extract_dates_asin_node`
- `classify_question_node`
- Handler nodes

## Files Created

```
evaluations/
├── __init__.py                          ✅ Package init
├── README.md                            ✅ Full documentation
├── QUICK_START.md                       ✅ This file
├── config.py                            ✅ LangSmith configuration
├── node_wrappers.py                     ✅ State conversion & date injection
├── run_date_extraction_eval.py          ✅ Main evaluation script
├── datasets/
│   ├── README.md                        ✅ Dataset upload instructions
│   └── dates_metrics_examples.csv       ✅ 20 test examples
└── evaluators/
    ├── __init__.py                      ✅ Evaluators package init
    └── date_accuracy.py                 ✅ Custom evaluators

Main node files remain clean - no modifications! ✅
```

## Summary

1. ✅ **Dataset ready**: `dates_metrics_examples.csv` with 20 examples
2. ✅ **Upload to LangSmith**: Use web console (name: `nyle-dates-metrics-dataset`)
3. ✅ **Run evaluation**: `python evaluations/run_date_extraction_eval.py`
4. ✅ **View results**: LangSmith UI → Experiments
5. ✅ **All isolated**: Main node files unchanged

**Dataset Format**: 4 columns (`question`, `current_date`, `date_start`, `date_end`)
**Dataset Name**: `nyle-dates-metrics-dataset`
**Key Design**: Fixed `current_date` for reproducible testing

