#!/usr/bin/env python3
"""
Classifier Evaluation Script

Tests the classifier node with questions and validates the output question_type.
"""

import sys
import os
import csv
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.graph.nodes.classifier.node import classify_question_node
from app.models.agentState import AgentState

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_classifier_eval():
    """
    Run classifier evaluation on dataset.
    """
    dataset_path = Path(__file__).parent / "dataset.csv"
    
    if not dataset_path.exists():
        logger.error(f"Dataset not found: {dataset_path}")
        return
    
    # Read dataset
    test_cases = []
    with open(dataset_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        test_cases = list(reader)
    
    logger.info(f"Loaded {len(test_cases)} test cases")
    
    # Run evaluation
    results = []
    correct = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        question = test_case['question']
        expected_type = test_case['question_type']
        
        logger.info(f"\n[{i}/{total}] Testing: {question}")
        logger.info(f"Expected: {expected_type}")
        
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
        import re
        asin_match = re.search(r'B[0-9A-Z]{9}', question)
        if asin_match:
            state['asin'] = asin_match.group(0)
        
        # Run classifier
        try:
            result_state = classify_question_node(state)
            predicted_type = result_state['question_type']
            
            is_correct = predicted_type == expected_type
            if is_correct:
                correct += 1
            
            logger.info(f"Predicted: {predicted_type} | {'✅ CORRECT' if is_correct else '❌ WRONG'}")
            
            results.append({
                'question': question,
                'expected_type': expected_type,
                'predicted_type': predicted_type,
                'correct': is_correct
            })
            
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            results.append({
                'question': question,
                'expected_type': expected_type,
                'predicted_type': 'ERROR',
                'correct': False
            })
    
    # Calculate accuracy
    accuracy = (correct / total) * 100 if total > 0 else 0
    
    # Print summary
    print("\n" + "="*80)
    print("EVALUATION SUMMARY")
    print("="*80)
    print(f"Total test cases: {total}")
    print(f"Correct: {correct}")
    print(f"Incorrect: {total - correct}")
    print(f"Accuracy: {accuracy:.2f}%")
    print("="*80)
    
    # Show incorrect predictions
    incorrect_results = [r for r in results if not r['correct']]
    if incorrect_results:
        print("\nINCORRECT PREDICTIONS:")
        print("-"*80)
        for r in incorrect_results:
            print(f"Question: {r['question']}")
            print(f"Expected: {r['expected_type']}")
            print(f"Predicted: {r['predicted_type']}")
            print("-"*80)
    
    # Save results to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(__file__).parent / f"results_{timestamp}.csv"
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['question', 'expected_type', 'predicted_type', 'correct']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"\nResults saved to: {output_path}")
    
    return accuracy, results


if __name__ == "__main__":
    run_classifier_eval()

