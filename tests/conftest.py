import pytest
import os

# Set test environment
os.environ["ENVIRONMENT"] = "local"
os.environ["OPENAI_API_KEY"] = "test-key"


@pytest.fixture
def sample_state():
    """Return a sample AgentState for testing."""
    return {
        "messages": [],
        "question": "What is my ACOS?",
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


@pytest.fixture
def comparison_state():
    """Return a sample state for comparison queries."""
    return {
        "messages": [],
        "question": "Compare August vs September",
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


@pytest.fixture
def asin_state():
    """Return a sample state for ASIN queries."""
    return {
        "messages": [],
        "question": "What are sales for ASIN B0B5HN65QQ?",
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

