import re
import logging

from app.models.agentState import AgentState

logger = logging.getLogger(__name__)


def classify_question_node(state: AgentState) -> AgentState:
    """
    Classify question based on ASIN presence.
    
    Rule:
    - asin_product: Question contains "ASIN"/"ASINs" OR asin param is not null
    - metrics_query: Everything else
    """
    
    question = state.get("question", "")
    asin = state.get("asin")
    http_asin = state.get("_http_asin")
    
    logger.info(f"Classifying: '{question}'")
    
    # Check if question contains ASIN/ASINs (case insensitive)
    has_asin_word = bool(re.search(r'\bASINs?\b', question, re.IGNORECASE))
    has_asin_param = bool(asin or http_asin)
    
    if has_asin_word or has_asin_param:
        question_type = "asin_product"
        logger.info(f"Classified as asin_product (has_asin_word={has_asin_word}, has_asin_param={has_asin_param})")
    else:
        question_type = "metrics_query"
        logger.info(f"Classified as metrics_query (no ASIN detected)")
    
    state["question_type"] = question_type
    
    return state
