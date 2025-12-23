"""
Main script to run LangSmith evaluation for extract_dates_metrics_node.

Usage:
    python evaluations/run_date_extraction_eval.py

Prerequisites:
1. Set LANGSMITH_API_KEY environment variable (or have it in .env.local)
2. Upload dataset to LangSmith web console:
   - Name: nyle-dates-metrics-dataset
   - File: evaluations/datasets/dates_metrics_examples.csv
   - Inputs: question, current_date
   - Outputs: date_start, date_end
"""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")

# Add project root to path so we can import app modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from langsmith import aevaluate

from evaluations.config import EvaluationConfig
from evaluations.node_wrappers import create_dates_metrics_target
from evaluations.evaluators import (
    exact_date_match,
    date_validity_check,
    date_logic_check,
    date_extraction_accuracy
)


async def run_evaluation():
    """
    Run LangSmith evaluation on extract_dates_metrics_node.
    
    This will:
    1. Load the dataset from LangSmith
    2. Run the node on each example
    3. Apply custom evaluators
    4. Log results as an experiment in LangSmith
    """
    # Validate configuration
    print("🔍 Validating configuration...")
    EvaluationConfig.validate()
    print(f"✅ LangSmith project: {EvaluationConfig.LANGSMITH_PROJECT}")
    print(f"✅ Dataset: {EvaluationConfig.DATES_METRICS_DATASET}")
    
    # Create node target
    print("\n🔧 Creating evaluation target...")
    node_target = create_dates_metrics_target()
    print("✅ Node target created: example_to_state | extract_dates_metrics_node")
    
    # Define evaluators
    evaluators = [
        exact_date_match,
        date_validity_check,
        date_logic_check,
        date_extraction_accuracy
    ]
    print(f"✅ Loaded {len(evaluators)} evaluators")
    
    # Run evaluation
    print(f"\n🚀 Starting evaluation...")
    print(f"   Dataset: {EvaluationConfig.DATES_METRICS_DATASET}")
    print(f"   Concurrency: {EvaluationConfig.MAX_CONCURRENCY}")
    print(f"   Experiment prefix: {EvaluationConfig.DATES_METRICS_EXPERIMENT_PREFIX}")
    print("\nThis may take a few minutes...\n")
    
    try:
        results = await aevaluate(
            node_target,
            data=EvaluationConfig.DATES_METRICS_DATASET,
            evaluators=evaluators,
            max_concurrency=EvaluationConfig.MAX_CONCURRENCY,
            experiment_prefix=EvaluationConfig.DATES_METRICS_EXPERIMENT_PREFIX
        )
        
        print("\n✅ Evaluation complete!")
        print("\n📊 Results Summary:")
        
        # AsyncExperimentResults object has different attributes
        if hasattr(results, 'experiment_name'):
            print(f"   Experiment: {results.experiment_name}")
        
        if hasattr(results, 'results'):
            total_examples = len(results.results)
            print(f"   Total examples evaluated: {total_examples}")
            
            # Try to calculate pass rate from the results
            if total_examples > 0:
                try:
                    passed = sum(1 for r in results.results 
                               if hasattr(r, 'evaluation_results') 
                               and r.evaluation_results 
                               and any(e.score == 1.0 
                                     for e in r.evaluation_results.get('results', [])
                                     if hasattr(e, 'score')))
                    print(f"   Examples with passing scores: {passed}/{total_examples}")
                except:
                    pass
        
        print("\n🔗 View Detailed Results in LangSmith:")
        print(f"   1. Go to https://smith.langchain.com")
        print(f"   2. Navigate to 'Experiments' tab")
        print(f"   3. Find experiment: {EvaluationConfig.DATES_METRICS_EXPERIMENT_PREFIX}")
        print(f"   4. Click to view:")
        print(f"      • Individual test case results")
        print(f"      • Evaluator scores (exact_match, validity, logic)")
        print(f"      • Full traces with LLM calls")
        print(f"      • Input/output comparisons")
        
    except Exception as e:
        print(f"\n❌ Evaluation failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Ensure LANGSMITH_API_KEY is set correctly")
        print("2. Verify dataset exists in LangSmith with name: nyle-dates-metrics-dataset")
        print("3. Check that dataset has correct input/output columns")
        print("4. Review error message above for details")
        raise


def main():
    """Entry point for the evaluation script."""
    print("=" * 60)
    print("LangSmith Evaluation: extract_dates_metrics_node")
    print("=" * 60)
    
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

