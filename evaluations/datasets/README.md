# LangSmith Dataset Upload Instructions

## Dataset: dates_metrics_examples.csv

This CSV file contains test examples for evaluating the `extract_dates_metrics_node`.

### How to Upload to LangSmith Web Console

1. **Go to LangSmith UI**: https://smith.langchain.com
2. **Navigate to Datasets**: Click "Datasets" in the left sidebar
3. **Create New Dataset**: Click "+ New Dataset" button
4. **Dataset Details**:
   - **Name**: `nyle-dates-metrics-dataset`
   - **Description**: Date extraction evaluation for metrics queries with fixed current_date for reproducibility
5. **Upload CSV**: Click "Upload CSV" and select `dates_metrics_examples.csv`
6. **Configure Columns**:
   - **Input columns**: `question`, `current_date`
   - **Output columns**: `date_start`, `date_end`
7. **Confirm**: Click "Create Dataset"

### CSV Format

The CSV has 4 columns:

| Column | Type | Description |
|--------|------|-------------|
| `question` | Input | Natural language time reference question |
| `current_date` | Input | Fixed reference date (YYYY-MM-DD) for reproducibility |
| `date_start` | Output | Expected start date (YYYY-MM-DD) |
| `date_end` | Output | Expected end date (YYYY-MM-DD) |

### Why Fixed Dates?

Using **fixed `current_date`** values ensures:
- ✅ Tests are reproducible (same results every time)
- ✅ Can test edge cases (month/year boundaries, leap years)
- ✅ CI/CD reliability (tests don't fail just because a day passed)
- ✅ Version control friendly (static expected outputs)

### Example Rows

```csv
question,current_date,date_start,date_end
"Show me last week's sales","2025-12-22","2025-12-15","2025-12-21"
"What was yesterday's performance?","2025-12-22","2025-12-21","2025-12-21"
```

When the evaluator runs with `current_date="2025-12-22"`:
- "last week" should extract `2025-12-15` to `2025-12-21`
- "yesterday" should extract `2025-12-21` to `2025-12-21`

### Adding More Examples

To expand the dataset:
1. Add rows to the CSV
2. Re-upload to LangSmith (it will update the existing dataset)
3. Include diverse time references: "last month", "Q3", "today", "past 14 days", etc.


