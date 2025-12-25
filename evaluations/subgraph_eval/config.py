"""
They're separate so your new subgraph evaluation doesn't interfere with your existing evaluations. Each evaluation type has its own isolated configuration.
Configuration for 3-node subgraph evaluation.
"""
import os


class SubgraphEvalConfig:
    """Configuration settings for subgraph evaluation."""
    
    # LangSmith settings
    LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "nyle-chatbot")
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
    
    # Dataset (must match name in LangSmith web console)
    DATASET_NAME = "nyle-subgraph-dataset"
    
    # Experiment settings
    EXPERIMENT_PREFIX = "subgraph-eval"
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


