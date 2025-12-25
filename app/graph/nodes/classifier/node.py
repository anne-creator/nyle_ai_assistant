from langchain_openai import ChatOpenAI
import logging

from app.models.agentState import AgentState
from app.config import get_settings
from app.graph.nodes.classifier.prompt import CLASSIFIER_PROMPT

logger = logging.getLogger(__name__)


def classify_question_node(state: AgentState) -> AgentState:
    """
    Classify question into one of 5 types.
    
    Types:
    - metrics_query: Regular metric questions (ACOS, sales, profit, etc.)
    - compare_query: Comparison questions (August vs September, Q1 vs Q2)
    - asin_product: ASIN-specific questions (about a specific product)
    - hardcoded: Questions with hardcoded responses
    - other: Questions that don't fit into any category
    """
    
    logger.info(f"Classifying: '{state['question']}'")
    
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key
    )
    
    prompt = CLASSIFIER_PROMPT.format(question=state["question"])
    
    response = llm.invoke(prompt)
    question_type = response.content.strip().lower()
    
    # Validate category
    valid_types = ["metrics_query", "compare_query", "asin_product", "hardcoded", "other"]
    if question_type not in valid_types:
        logger.warning(f"Invalid category '{question_type}', defaulting to other")
        question_type = "other"
    
    # Always classify as asin_product if ASIN params are present
    asin = state.get("asin")
    http_asin = state.get("_http_asin")
    if asin or http_asin:
        original_type = question_type
        question_type = "asin_product"
        logger.info(f"🔄 Override: Re-classified from '{original_type}' to 'asin_product' due to ASIN presence (asin={asin}, _http_asin={http_asin})")
    
    state["question_type"] = question_type
    logger.info(f"Question type: {question_type}")
    
    return state

