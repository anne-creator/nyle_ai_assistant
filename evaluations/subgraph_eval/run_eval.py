"""
Run LangSmith evaluation for the 3-node subgraph.

Subgraph: label_normalizer -> message_analyzer -> extractor_evaluator -> date_calculator

Usage:
    python evaluations/subgraph_eval/run_eval.py

Prerequisites:
1. Set LANGSMITH_API_KEY environment variable
2. Upload dataset to LangSmith web console:
   - Name: nyle-subgraph-dataset
   - File: evaluations/subgraph_eval/dataset.csv
   - Inputs: question, current_date, http_asin, http_date_start, http_date_end, sessionid
   - Outputs: node1_*, node2_* columns
"""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env.local")

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from langsmith import aevaluate

from evaluations.subgraph_eval.config import SubgraphEvalConfig
from evaluations.subgraph_eval.wrappers import create_subgraph_target
from evaluations.subgraph_eval.evaluators import (
    # Node 1 evaluators
    node1_date_start_label,
    node1_date_end_label,
    node1_asin,
    node1_compare_labels,
    node1_custom_days,
    node1_explicit_dates,
    node1_explicit_compare_dates,
    # Node 2 evaluators
    node2_date_start,
    node2_date_end,
    node2_compare_dates,
    node2_date_validity,
    node2_date_logic,
    # Pass-through evaluators
    normalizer_valid_passthrough,
    normalizer_retries_passthrough,
    normalizer_feedback_passthrough,
    # Combined evaluator
    pipeline_accuracy
)


async def run_evaluation():
    """
    Run LangSmith evaluation on the 3-node subgraph.
    
    Evaluates:
    - Node 1 (label_normalizer): Label extraction accuracy
    - Node 2 (message_analyzer): Pass-through
    - Node 3 (extractor_evaluator): Pass-through
    - Date Calculator: Date calculation accuracy
    """
    print("🔍 Validating configuration...")
    SubgraphEvalConfig.validate()
    print(f"✅ LangSmith project: {SubgraphEvalConfig.LANGSMITH_PROJECT}")
    print(f"✅ Dataset: {SubgraphEvalConfig.DATASET_NAME}")
    
    print("\n🔧 Creating subgraph evaluation target...")
    subgraph_target = create_subgraph_target()
    print("✅ Subgraph: label_normalizer → message_analyzer → extractor_evaluator → date_calculator")
    
    # All evaluators
    evaluators = [
        # Node 1: Label extraction
        node1_date_start_label,
        node1_date_end_label,
        node1_asin,
        node1_compare_labels,
        node1_custom_days,
        node1_explicit_dates,
        node1_explicit_compare_dates,
        # Node 2: Date calculation
        node2_date_start,
        node2_date_end,
        node2_compare_dates,
        node2_date_validity,
        node2_date_logic,
        # Pass-through (metadata capture)
        normalizer_valid_passthrough,
        normalizer_retries_passthrough,
        normalizer_feedback_passthrough,
        # Combined
        pipeline_accuracy
    ]
    print(f"✅ Loaded {len(evaluators)} evaluators")
    
    print("\n📊 Evaluator Standards:")
    print("   Node 1 (label_normalizer):")
    print("     - date_start_label, date_end_label: Exact match")
    print("     - asin: Exact match (empty = no ASIN)")
    print("     - compare_labels: Exact match for comparison queries")
    print("     - custom_days: Exact match for 'past X days' queries")
    print("     - explicit_dates: Exact match for specific date queries")
    print("   Node 2 (date_calculator):")
    print("     - date_start, date_end: Exact match (YYYY-MM-DD)")
    print("     - compare_dates: Exact match for comparison queries")
    print("     - date_validity: Valid YYYY-MM-DD format")
    print("     - date_logic: start <= end")
    print("   Pass-through (always 1.0):")
    print("     - normalizer_valid, normalizer_retries, normalizer_feedback")
    
    print(f"\n🚀 Starting evaluation...")
    print(f"   Dataset: {SubgraphEvalConfig.DATASET_NAME}")
    print(f"   Concurrency: {SubgraphEvalConfig.MAX_CONCURRENCY}")
    print(f"   Experiment prefix: {SubgraphEvalConfig.EXPERIMENT_PREFIX}")
    print("\nThis may take a few minutes...\n")
    
    try:
        results = await aevaluate(
            subgraph_target,
            data=SubgraphEvalConfig.DATASET_NAME,
            evaluators=evaluators,
            max_concurrency=SubgraphEvalConfig.MAX_CONCURRENCY,
            experiment_prefix=SubgraphEvalConfig.EXPERIMENT_PREFIX
        )
        
        print("\n✅ Evaluation complete!")
        print("\n📊 Results Summary:")
        
        if hasattr(results, 'experiment_name'):
            print(f"   Experiment: {results.experiment_name}")
        
        print("\n🔗 View Detailed Results in LangSmith:")
        print(f"   1. Go to https://smith.langchain.com")
        print(f"   2. Navigate to 'Experiments' tab")
        print(f"   3. Find experiment: {SubgraphEvalConfig.EXPERIMENT_PREFIX}-*")
        print(f"   4. Inspect per-node outputs:")
        print(f"      • Node 1: _date_start_label, _date_end_label, asin, etc.")
        print(f"      • Node 2: date_start, date_end, compare_date_start, etc.")
        print(f"      • Metadata: _normalizer_valid, _normalizer_retries")
        
    except Exception as e:
        print(f"\n❌ Evaluation failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Ensure LANGSMITH_API_KEY is set correctly")
        print(f"2. Verify dataset exists in LangSmith: {SubgraphEvalConfig.DATASET_NAME}")
        print("3. Check dataset columns match expected inputs/outputs")
        print("4. Ensure all app dependencies are installed")
        raise


def main():
    """Entry point."""
    print("=" * 70)
    print("LangSmith Evaluation: 3-Node Subgraph")
    print("(label_normalizer → message_analyzer → extractor_evaluator → date_calculator)")
    print("=" * 70)
    
    try:
        asyncio.run(run_evaluation())
    except KeyboardInterrupt:
        print("\n\n⚠️  Evaluation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()



