#!/usr/bin/env python3
"""
Quick Test Script for Classifier

Tests a single question through the classifier for debugging purposes.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.graph.nodes.classifier.node import classify_question_node
from app.models.agentState import AgentState
import re


def test_single_question(question: str):
    """Test a single question through the classifier."""
    
    print(f"\n{'='*80}")
    print(f"Testing Question: {question}")
    print(f"{'='*80}")
    
    # Create minimal state
    state = AgentState(
        messages=[],
        question=question,
        _http_date_start=None,
        _http_date_end=None,
        _http_asin=None,
        _date_start_label=None,
        _date_end_label=None,
        _compare_date_start_label=None,
        _compare_date_end_label=None,
        _explicit_date_start=None,
        _explicit_date_end=None,
        _explicit_compare_start=None,
        _explicit_compare_end=None,
        _custom_days_count=None,
        _custom_compare_days_count=None,
        date_start="",
        date_end="",
        compare_date_start=None,
        compare_date_end=None,
        asin=None,
        _normalizer_valid=None,
        _normalizer_retries=None,
        _normalizer_feedback=None,
        question_type="metrics_query",  # default
        requested_metrics=None,
        metric_data=None,
        comparison_metric_data=None,
        response=""
    )
    
    # Check if ASIN is in question and set it
    asin_match = re.search(r'B[0-9A-Z]{9}', question)
    if asin_match:
        state['asin'] = asin_match.group(0)
        print(f"Detected ASIN: {asin_match.group(0)}")
    
    # Run classifier
    try:
        result_state = classify_question_node(state)
        predicted_type = result_state['question_type']
        
        print(f"\n✅ Classification Result: {predicted_type}")
        print(f"{'='*80}\n")
        
        return predicted_type
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"{'='*80}\n")
        return None


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Use command line argument
        question = " ".join(sys.argv[1:])
        test_single_question(question)
    else:
        # Interactive mode
        print("\nClassifier Quick Test")
        print("="*80)
        print("Enter a question to classify (or 'quit' to exit)")
        print("="*80)
        
        while True:
            question = input("\nQuestion: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not question:
                print("Please enter a question.")
                continue
            
            test_single_question(question)



