# Classifier Evaluation

This folder contains tools for evaluating the question classifier node.

## Overview

The classifier evaluation tests the `classify_question_node` to ensure it correctly categorizes questions into one of four types:

1. **metrics_query** - Questions about store-level metrics
2. **compare_query** - Questions comparing TWO time periods  
3. **asin_product** - Questions about a SPECIFIC product (ASIN)
4. **hardcoded** - Questions with hardcoded responses

## Files

- `dataset.csv` - Test dataset with questions and expected classifications
- `run_eval.py` - Main evaluation script
- `test_single.py` - Quick test script for single questions
- `config.py` - Configuration and constants
- `__init__.py` - Package initialization

## Dataset

The dataset contains 39 test questions:
- 15 questions from the original subgraph evaluation dataset
- 24 additional questions with variations in phrasing and intent

Questions vary in:
- Formality (formal vs casual)
- Phrasing (direct vs indirect)
- Intent (what, how, show me, etc.)
- Specificity (specific metrics vs general performance)

## Running the Evaluation

### Full Evaluation

From the project root:

```bash
python evaluations/classifier_eval/run_eval.py
```

Or from the classifier_eval folder:

```bash
cd evaluations/classifier_eval
python run_eval.py
```

### Quick Single Question Test

Test a single question for debugging:

```bash
# From project root
python evaluations/classifier_eval/test_single.py "what is my roi today?"

# Or interactive mode
python evaluations/classifier_eval/test_single.py
```

## Output

The script will:
1. Load the test dataset
2. Run each question through the classifier
3. Compare predicted types with expected types
4. Display results including:
   - Total accuracy
   - Correct vs incorrect counts
   - List of any misclassifications
5. Save detailed results to `results_YYYYMMDD_HHMMSS.csv`

## Example Output

```
================================================================================
EVALUATION SUMMARY
================================================================================
Total test cases: 39
Correct: 37
Incorrect: 2
Accuracy: 94.87%
================================================================================
```

## Dataset Structure

The CSV has two columns:

- `question` - The test question
- `question_type` - Expected classification (metrics_query, compare_query, asin_product, or hardcoded)

Example:
```csv
question,question_type
"what is todays store overall performance",metrics_query
"compare my roi from sep to Dec",compare_query
"show me product B0B5HN65QQ performance",asin_product
"Show me performance insights",hardcoded
```

