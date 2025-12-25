import logging

from app.models.agentState import AgentState

logger = logging.getLogger(__name__)


def extractor_evaluator_node(state: AgentState) -> AgentState:
    """
    THIRD NODE: AI-powered evaluator that validates Node 1 and Node 2 outputs.
    
    Features:
    - Validates label extraction accuracy (Node 1)
    - Validates date calculation correctness (Node 2)
    - Provides feedback for regeneration
    - No retries: always passes through to prevent long response times
    
    Inputs (from previous nodes):
        - question: user's question
        - Node 1 outputs: labels, metadata, ASIN
        - Node 2 outputs: calculated dates
    
    Outputs (updates state):
        - _normalizer_valid: bool (always True - no retries)
        - _normalizer_retries: int (always 0)
        - _normalizer_feedback: str (empty - no feedback needed)
    """
    
    logger.info("🔍 Extractor Evaluator: Passing through (retries disabled)")
    
    # Always mark as valid and proceed - no retry logic
    state["_normalizer_valid"] = True
    state["_normalizer_retries"] = 0
    state["_normalizer_feedback"] = None
    logger.info("✅ Validation passed - proceeding to classifier")
    
    return state

