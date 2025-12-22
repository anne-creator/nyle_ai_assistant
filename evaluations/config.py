"""
Configuration for LangSmith evaluations.
"""
import os

class EvaluationConfig:
    """Configuration settings for running LangSmith evaluations."""
    
    # LangSmith project settings
    LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "nyle-chatbot")
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
    
    # Dataset names (must match names in LangSmith web console)
    DATES_METRICS_DATASET = "nyle-dates-metrics-dataset"
    
    # Experiment settings
    DATES_METRICS_EXPERIMENT_PREFIX = "dates-metrics-eval"
    MAX_CONCURRENCY = 4
    
    @classmethod
    def validate(cls):
        """Validate required configuration is present."""
        if not cls.LANGSMITH_API_KEY:
            raise ValueError(
                "LANGSMITH_API_KEY not found in environment. "
                "Please set it: export LANGSMITH_API_KEY='your-key-here'"
            )
        return True

