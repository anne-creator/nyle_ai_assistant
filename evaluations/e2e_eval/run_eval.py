"""
Run LangSmith evaluation for end-to-end graph execution.

This evaluation runs the complete graph from start to finish without HTTP calls.

Usage:
    python evaluations/e2e_eval/run_eval.py

Prerequisites:
1. Set LANGSMITH_API_KEY environment variable
2. Upload dataset to LangSmith web console:
   - Name: nyle-e2e-dataset
   - File: evaluations/e2e_eval/dataset.csv
   - Inputs: question, current_date, http_asin, http_date_start, http_date_end, sessionid
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

from evaluations.e2e_eval.config import E2EEvalConfig
from evaluations.e2e_eval.wrappers import create_e2e_target
from evaluations.e2e_eval.evaluators import (
    response_completeness,
    graph_execution_success,
    final_answer_presence,
    nodes_executed,
    pipeline_success
)


async def run_evaluation():
    """
    Run LangSmith evaluation on the complete graph end-to-end.
    
    Evaluates:
    - Complete graph execution without HTTP calls
    - Response completeness
    - Node execution tracking
    - Overall pipeline success
    """
    print("🔍 Validating configuration...")
    E2EEvalConfig.validate()
    print(f"✅ LangSmith project: {E2EEvalConfig.LANGSMITH_PROJECT}")
    print(f"✅ Dataset: {E2EEvalConfig.DATASET_NAME}")
    
    print("\n🔧 Creating end-to-end evaluation target...")
    e2e_target = create_e2e_target()
    print("✅ Target: Complete graph execution (no HTTP calls)")
    
    # All evaluators
    evaluators = [
        response_completeness,
        graph_execution_success,
        final_answer_presence,
        nodes_executed,
        pipeline_success
    ]
    print(f"✅ Loaded {len(evaluators)} evaluators")
    
    print("\n📊 Evaluator Standards:")
    print("   Response Completeness:")
    print("     - Checks if response exists and is not an error")
    print("   Graph Execution Success:")
    print("     - Verifies graph completed without errors")
    print("   Final Answer Presence:")
    print("     - Confirms final answer was generated")
    print("   Nodes Executed:")
    print("     - Tracks which nodes were executed in the graph")
    print("   Pipeline Success:")
    print("     - Combined check of all success indicators")
    
    print(f"\n🚀 Starting evaluation...")
    print(f"   Dataset: {E2EEvalConfig.DATASET_NAME}")
    print(f"   Concurrency: {E2EEvalConfig.MAX_CONCURRENCY}")
    print(f"   Experiment prefix: {E2EEvalConfig.EXPERIMENT_PREFIX}")
    print("\nThis may take a few minutes...\n")
    
    try:
        results = await aevaluate(
            e2e_target,
            data=E2EEvalConfig.DATASET_NAME,
            evaluators=evaluators,
            max_concurrency=E2EEvalConfig.MAX_CONCURRENCY,
            experiment_prefix=E2EEvalConfig.EXPERIMENT_PREFIX
        )
        
        print("\n✅ Evaluation complete!")
        print("\n📊 Results Summary:")
        
        if hasattr(results, 'experiment_name'):
            print(f"   Experiment: {results.experiment_name}")
        
        print("\n🔗 View Detailed Results in LangSmith:")
        print(f"   1. Go to https://smith.langchain.com")
        print(f"   2. Navigate to 'Experiments' tab")
        print(f"   3. Find experiment: {E2EEvalConfig.EXPERIMENT_PREFIX}-*")
        print(f"   4. Inspect outputs:")
        print(f"      • response: Final response text")
        print(f"      • final_answer: Final answer from graph")
        print(f"      • nodes_executed: List of executed nodes")
        print(f"      • error: Any errors encountered")
        
    except Exception as e:
        print(f"\n❌ Evaluation failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Ensure LANGSMITH_API_KEY is set correctly")
        print(f"2. Verify dataset exists in LangSmith: {E2EEvalConfig.DATASET_NAME}")
        print("3. Check dataset columns match expected inputs")
        print("4. Ensure all app dependencies are installed")
        raise


def main():
    """Entry point."""
    print("=" * 70)
    print("LangSmith Evaluation: End-to-End Graph Execution")
    print("(Complete graph without HTTP calls)")
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

