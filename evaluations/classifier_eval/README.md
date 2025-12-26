# Classifier Evaluation
It does not go tot eh langSmith, coz it is a simple test case, so we just test it using temrinal, it will print all incorrect predictions.
This folder contains tools for evaluating the question classifier node.

## Overview

The classifier evaluation tests the `classify_question_node` to ensure it correctly categorizes questions into one of five types:

1. **metrics_query** - Questions about store-level metrics
2. **compare_query** - Questions comparing TWO time periods
3. **asin_product** - Questions about a SPECIFIC product (ASIN)
4. **hardcoded** - Questions with hardcoded responses
5. **other_query** - General questions, greetings, definitions, or questions not related to business metrics

## Files

- `dataset.csv` - Test dataset with questions and expected classifications
- `run_eval.py` - Main evaluation script
- `test_single.py` - Quick test script for single questions
- `config.py` - Configuration and constants
- `__init__.py` - Package initialization

## Dataset

The dataset contains 60 test questions including:
- Core questions testing keyword-based classification
- Edge cases testing AgentState-based classification
- Questions with various phrasings and intents

Questions test:
- **Keyword detection**: "ASIN", "compare", "versus", etc.
- **State-based detection**: asin param set, compare_date_start set
- **AI classification**: metrics_query vs other (general questions)
- **Hardcoded responses**: Exact string matching

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

The CSV has five columns:

- `question` - The test question
- `question_type` - Expected classification (metrics_query, compare_query, asin_product, hardcoded, or other_query)
- `asin` - (Optional) Pre-inject ASIN into AgentState (simulates label_normalizer output)
- `_http_asin` - (Optional) Pre-inject HTTP ASIN param into AgentState (simulates HTTP request)
- `compare_date_start` - (Optional) Pre-inject compare date into AgentState (simulates message_analyzer output)

### State Preset Columns

The last three columns allow testing the classifier with **realistic AgentState** values that would be set by previous nodes:

- **`asin`**: Simulates when label_normalizer extracts an ASIN from the question
- **`_http_asin`**: Simulates when ASIN is passed via HTTP request parameter
- **`compare_date_start`**: Simulates when message_analyzer detects comparison dates

Leave these columns empty for most tests. Use them for **edge cases** where:
- Question doesn't contain "ASIN" keyword but ASIN is in state
- Question doesn't contain comparison keywords but compare_date_start is set

Example:
```csv
question,question_type,asin,_http_asin,compare_date_start
"what is todays store overall performance",metrics_query,,,
"compare my roi from sep to Dec",compare_query,,,
"show me product B0B5HN65QQ performance",asin_product,B0B5HN65QQ,,
"Show me performance insights",hardcoded,,,
"Show me the performance for this product",asin_product,,B0TEST1234,
"What's the sales trend?",compare_query,,,2024-09-01
```

