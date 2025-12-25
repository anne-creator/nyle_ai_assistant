"""
Configuration for Classifier Evaluation

This module contains configuration settings for the classifier evaluation.
"""

# Question type categories
QUESTION_TYPES = [
    "metrics_query",
    "compare_query",
    "asin_product",
    "hardcoded"
]

# Question type descriptions
QUESTION_TYPE_DESCRIPTIONS = {
    "metrics_query": "Questions about store-level metrics (ACOS, sales, profit, etc.)",
    "compare_query": "Questions comparing TWO time periods",
    "asin_product": "Questions about a SPECIFIC product (ASIN)",
    "hardcoded": "Questions with hardcoded responses"
}

