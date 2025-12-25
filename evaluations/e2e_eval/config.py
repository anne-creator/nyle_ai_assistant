"""
Configuration for end-to-end evaluation.
"""
import os


class E2EEvalConfig:
    """Configuration settings for end-to-end evaluation."""
    
    # LangSmith settings
    LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "nyle-chatbot")
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
    
    # Dataset (must match name in LangSmith web console)
    DATASET_NAME = "nyle-e2e-dataset"
    
    # Experiment settings
    EXPERIMENT_PREFIX = "e2e-eval"
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

