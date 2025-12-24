import logging

from app.models.agentState import AgentState

logger = logging.getLogger(__name__)


def message_analyzer_node(state: AgentState) -> AgentState:
    """
    Message analyzer: Currently does nothing (pass-through node).
    """
    
    logger.info("Message analyzer: doing nothing (pass-through mode)")
    
    # Pass through state without modification
    return state

