"""
LangSmith Dataset Evaluation Script.

Reads a CSV file with questions, answers, and API endpoints, creates a LangSmith dataset,
and runs evaluation against a deployed agent URL (dev or production based on ENVIRONMENT).

Usage:
    ENVIRONMENT=dev python evaluations/run_langsmith_dataset_eval.py --csv evaluations/outputs/e2e_results_20251222_201931.csv
    ENVIRONMENT=prod python evaluations/run_langsmith_dataset_eval.py --csv evaluations/outputs/e2e_results_20251222_201931.csv
"""
import argparse
import csv
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

from dotenv import load_dotenv
from langsmith import Client
from langchain.smith import run_on_dataset
import requests

# Load environment variables
project_root = Path(__file__).parent.parent
env = os.getenv("ENVIRONMENT", "dev").lower()
env_file = project_root / f".env.{env}"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
else:
    # Fallback to .env.local if specific env file doesn't exist
    load_dotenv(dotenv_path=project_root / ".env.local")

# Environment-based URL selection
ENV = os.getenv("ENVIRONMENT", "dev").lower()
DEV_AGENT_URL = os.getenv("DEV_AGENT_URL", "")
PROD_AGENT_URL = os.getenv("PROD_AGENT_URL", "")

if ENV == "prod" or ENV == "production":
    AGENT_URL = PROD_AGENT_URL
    if not AGENT_URL:
        raise ValueError(
            "PROD_AGENT_URL not set in environment. "
            "Please set it in your .env file: PROD_AGENT_URL=https://your-prod-url"
        )
else:
    AGENT_URL = DEV_AGENT_URL
    if not AGENT_URL:
        raise ValueError(
            "DEV_AGENT_URL not set in environment. "
            "Please set it in your .env file: DEV_AGENT_URL=https://your-dev-url"
        )


def read_csv_examples(csv_path: Path) -> List[Dict[str, Any]]:
    """
    Read CSV file and convert to LangSmith dataset format.
    
    Expected CSV columns:
    - question: The question text
    - answer: The expected answer (may contain newlines)
    - api_endpoints_called: Comma-separated list of endpoints (e.g., "total,cfo")
    
    Returns:
        List of examples in LangSmith format:
        {
            "inputs": {"question": "..."},
            "outputs": {"answer": "..."},
            "metadata": {"api_endpoints_called": ["total", "cfo"]}
        }
    """
    examples = []
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            question = row.get("question", "").strip()
            answer = row.get("answer", "").strip()
            endpoints_str = row.get("api_endpoints_called", "").strip()
            
            # Parse endpoints: split by comma and clean up
            if endpoints_str:
                api_endpoints = [ep.strip() for ep in endpoints_str.split(",") if ep.strip()]
            else:
                api_endpoints = []
            
            if not question:
                print(f"Warning: Skipping row with empty question")
                continue
            
            examples.append({
                "inputs": {"question": question},
                "outputs": {"answer": answer},
                "metadata": {"api_endpoints_called": api_endpoints}
            })
    
    return examples


def create_langsmith_dataset(client: Client, dataset_name: str, examples: List[Dict[str, Any]]) -> Tuple[str, str]:
    """
    Create a LangSmith dataset from examples.
    
    Returns:
        Tuple of (dataset_id, dataset_name)
    """
    print(f"Creating dataset: {dataset_name}")
    
    # Check if dataset already exists
    try:
        existing = client.read_dataset(dataset_name=dataset_name)
        print(f"Dataset already exists with ID: {existing.id}")
        response = input("Do you want to use the existing dataset? (y/n): ").strip().lower()
        if response == "y":
            # Clear existing examples and add new ones
            print("Clearing existing examples...")
            existing_examples = list(client.list_examples(dataset_id=existing.id))
            for ex in existing_examples:
                client.delete_example(ex.id)
            print(f"Adding {len(examples)} examples to existing dataset...")
            client.create_examples(dataset_id=existing.id, examples=examples)
            return (existing.id, dataset_name)
        else:
            # Create new dataset with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_dataset_name = f"{dataset_name}_{timestamp}"
            print(f"Creating new dataset: {new_dataset_name}")
            dataset_name = new_dataset_name
    except Exception:
        # Dataset doesn't exist, create it
        pass
    
    dataset = client.create_dataset(dataset_name=dataset_name)
    print(f"Created dataset with ID: {dataset.id}")
    print(f"Adding {len(examples)} examples...")
    client.create_examples(dataset_id=dataset.id, examples=examples)
    
    return (dataset.id, dataset_name)


def call_env_agent(inputs: dict) -> dict:
    """
    Call the deployed agent URL with the question.
    
    Args:
        inputs: Dict with "question" key
        
    Returns:
        Dict with "answer" key
    """
    question = inputs.get("question", "")
    if not question:
        return {"answer": "ERROR: No question provided"}
    
    try:
        resp = requests.post(
            AGENT_URL,
            json={"question": question},
            timeout=60,
            headers={"Content-Type": "application/json"}
        )
        resp.raise_for_status()
        data = resp.json()
        
        # Extract answer from response
        # Adjust this based on your actual API response format
        answer = data.get("answer") or data.get("response") or str(data)
        
        return {"answer": answer}
    except requests.exceptions.RequestException as e:
        error_msg = f"ERROR: Request failed - {str(e)}"
        print(f"  {error_msg}")
        return {"answer": error_msg}
    except Exception as e:
        error_msg = f"ERROR: Unexpected error - {str(e)}"
        print(f"  {error_msg}")
        return {"answer": error_msg}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run LangSmith dataset evaluation against deployed agent"
    )
    parser.add_argument(
        "--csv",
        type=str,
        required=True,
        help="Path to CSV file with questions, answers, and api_endpoints_called"
    )
    parser.add_argument(
        "--dataset-name",
        type=str,
        default=None,
        help="Name for the LangSmith dataset (default: auto-generated)"
    )
    parser.add_argument(
        "--project-name",
        type=str,
        default=None,
        help="Name for the LangSmith project (default: auto-generated based on environment)"
    )
    parser.add_argument(
        "--skip-dataset-creation",
        action="store_true",
        help="Skip dataset creation and use existing dataset (requires --dataset-name)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("LangSmith Dataset Evaluation")
    print("=" * 60)
    print(f"Environment: {ENV}")
    print(f"Agent URL: {AGENT_URL}")
    print()
    
    # Validate LangSmith API key
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    if not langsmith_api_key:
        print("Error: LANGSMITH_API_KEY or LANGCHAIN_API_KEY not found in environment")
        sys.exit(1)
    
    # Initialize LangSmith client
    client = Client(api_key=langsmith_api_key)
    
    # Read CSV file
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)
    
    print(f"Reading CSV file: {csv_path}")
    examples = read_csv_examples(csv_path)
    print(f"Loaded {len(examples)} examples")
    print()
    
    # Create or use dataset
    if args.skip_dataset_creation:
        if not args.dataset_name:
            print("Error: --dataset-name required when using --skip-dataset-creation")
            sys.exit(1)
        try:
            dataset = client.read_dataset(dataset_name=args.dataset_name)
            dataset_id = dataset.id
            final_dataset_name = args.dataset_name
            print(f"Using existing dataset: {final_dataset_name} (ID: {dataset_id})")
        except Exception as e:
            print(f"Error: Could not find dataset '{args.dataset_name}': {e}")
            sys.exit(1)
    else:
        dataset_name = args.dataset_name or f"Store Agent – {ENV.title()} Tests"
        dataset_id, final_dataset_name = create_langsmith_dataset(client, dataset_name, examples)
        print(f"Dataset ready: {final_dataset_name} (ID: {dataset_id})")
        print()
    
    # Determine project name
    project_name = args.project_name or f"store-agent-eval-{ENV}"
    
    # Run evaluation
    print("=" * 60)
    print("Starting evaluation...")
    print(f"Project: {project_name}")
    print(f"Dataset: {dataset_id}")
    print(f"Agent URL: {AGENT_URL}")
    print("=" * 60)
    print()
    
    try:
        results = run_on_dataset(
            client=client,
            dataset_name=final_dataset_name,
            llm_or_chain_factory=lambda: call_env_agent,
            project_name=project_name,
            verbose=True,
        )
        
        print()
        print("=" * 60)
        print("Evaluation complete!")
        print(f"View results in LangSmith:")
        print(f"  Project: {project_name}")
        print(f"  Dataset: {final_dataset_name}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError during evaluation: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

