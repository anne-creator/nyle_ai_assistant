import logging

from app.models.agentState import AgentState

logger = logging.getLogger(__name__)


def extractor_evaluator_node(state: AgentState) -> AgentState:
    """
    Evaluate extracted data and prepare for classification.
    Currently a no-op for testing purposes.
    """
    
    logger.info("Extractor evaluator: doing nothing (testing mode)")
    
    # Pass through state without modification
    return state

