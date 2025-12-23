"""
End-to-End Metrics Evaluation Script.

Runs the full LangGraph chatbot on test questions with real API calls.
Records answers and tracks which Math Metrics API endpoints were called.

Usage:
    python evaluations/run_e2e_metrics_eval.py
"""
import asyncio
import csv
import getpass
import sys
import uuid
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import get_settings
from app.context import RequestContext
from app.graph.builder import create_chatbot_graph
from app.metricsAccessLayer import metrics_api
from evaluations.api_capture import init_capture, get_captured_endpoints_str, wrap_metrics_api
from evaluations.config import EvaluationConfig


def load_questions(csv_path: Path) -> list[str]:
    """Load questions from CSV file."""
    questions = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            questions.append(row["question"])
    return questions


async def run_single_question(graph, jwt_token: str, question: str, session_id: str) -> tuple[str, str]:
    """
    Run a single question through the graph.
    
    Returns:
        tuple of (answer, api_endpoints_called)
    """
    # Initialize capture for this request
    init_capture()
    
    # Build initial state
    initial_state = {
        "messages": [],
        "question": question,
        "date_start": "",
        "date_end": "",
        "compare_date_start": None,
        "compare_date_end": None,
        "asin": None,
        "question_type": "",
        "requested_metrics": None,
        "metric_data": None,
        "comparison_metric_data": None,
        "response": ""
    }
    
    # Run graph with request context
    with RequestContext(jwt_token=jwt_token, session_id=session_id):
        config = {"configurable": {"thread_id": session_id}}
        result = await graph.ainvoke(initial_state, config)
    
    answer = result.get("response", "")
    endpoints = get_captured_endpoints_str()
    
    return answer, endpoints


async def run_evaluation(jwt_token: str):
    """Run the full E2E evaluation."""
    
    # Validate configuration
    print("Validating configuration...")
    EvaluationConfig.validate()
    print(f"LangSmith project: {EvaluationConfig.LANGSMITH_PROJECT}")
    
    # Load settings to enable LangSmith tracing
    settings = get_settings()
    print(f"LangSmith tracing: {settings.langchain_tracing_v2}")
    
    # Wrap metrics_api to capture endpoint calls
    print("Setting up API capture...")
    wrap_metrics_api(metrics_api)
    
    # Create graph
    print("Creating chatbot graph...")
    graph = create_chatbot_graph()
    
    # Load questions
    csv_path = project_root / "evaluations" / "datasets" / EvaluationConfig.E2E_METRICS_DATASET
    print(f"Loading questions from: {csv_path}")
    questions = load_questions(csv_path)
    print(f"Loaded {len(questions)} questions")
    
    # Prepare output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = project_root / EvaluationConfig.E2E_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"e2e_results_{timestamp}.csv"
    
    # Run evaluation
    print(f"\nStarting evaluation...")
    print(f"Results will be saved to: {output_path}")
    print("-" * 60)
    
    results = []
    for i, question in enumerate(questions, 1):
        session_id = str(uuid.uuid4())
        print(f"[{i}/{len(questions)}] {question[:50]}...")
        
        try:
            answer, endpoints = await run_single_question(graph, jwt_token, question, session_id)
            results.append({
                "question": question,
                "answer": answer,
                "api_endpoints_called": endpoints
            })
            print(f"         -> endpoints: {endpoints or 'none'}")
        except Exception as e:
            print(f"         -> ERROR: {str(e)}")
            results.append({
                "question": question,
                "answer": f"ERROR: {str(e)}",
                "api_endpoints_called": ""
            })
    
    # Write results to CSV
    print("-" * 60)
    print(f"Writing results to: {output_path}")
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["question", "answer", "api_endpoints_called"])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\nEvaluation complete!")
    print(f"Total questions: {len(questions)}")
    print(f"Results saved to: {output_path}")
    print(f"\nView traces in LangSmith:")
    print(f"  1. Go to https://smith.langchain.com")
    print(f"  2. Navigate to project: {EvaluationConfig.LANGSMITH_PROJECT}")
    print(f"  3. Filter by run name containing: {EvaluationConfig.E2E_EXPERIMENT_PREFIX}")


def main():
    """Entry point."""
    print("=" * 60)
    print("E2E Metrics Evaluation")
    print("=" * 60)
    print()
    
    # Prompt for JWT token
    print("This evaluation requires a valid JWT token to call the Math Metrics API.")
    print("You can get this from your browser's dev tools when logged into Nyle.")
    print()
    
    jwt_token = getpass.getpass("Paste your JWT token (input hidden): ")
    
    if not jwt_token.strip():
        print("Error: JWT token cannot be empty")
        sys.exit(1)
    
    print()
    
    try:
        asyncio.run(run_evaluation(jwt_token.strip()))
    except KeyboardInterrupt:
        print("\n\nEvaluation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

