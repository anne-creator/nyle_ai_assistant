import re
import logging

from langchain_openai import ChatOpenAI

from app.models.agentState import AgentState
from app.config import get_settings
from app.graph.nodes.classifier.prompt import (
    HARDCODED_QUESTIONS,
    INSIGHT_KEYWORDS,
    METRICS_VS_OTHER_PROMPT
)

logger = logging.getLogger(__name__)


def _has_insight_keywords(question: str) -> bool:
    """Check if question contains insight/comparison keywords."""
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in INSIGHT_KEYWORDS)


def _is_hardcoded(question: str) -> bool:
    """Check if question matches a hardcoded response."""
    question_normalized = question.lower().strip()
    return question_normalized in HARDCODED_QUESTIONS


def _is_asin_query(question: str, state: AgentState) -> bool:
    """Check if question is about a specific ASIN/product."""
    # Check if ASIN param exists
    if state.get("asin") or state.get("_http_asin"):
        return True
    
    # Check if question contains ASIN keyword
    has_asin_word = bool(re.search(r'\bASINs?\b', question, re.IGNORECASE))
    return has_asin_word


def _classify_metrics_vs_other(question: str) -> str:
    """Use AI to classify between metrics_query and other_query."""
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key,
        streaming=True
    )
    
    prompt = METRICS_VS_OTHER_PROMPT.format(question=question)
    response = llm.invoke(prompt)
    question_type = response.content.strip().lower()
    
    # Validate category
    if question_type not in ["metrics_query", "other_query"]:
        logger.warning(f"Invalid AI classification '{question_type}', defaulting to other_query")
        question_type = "other_query"
    
    return question_type


def classify_question_node(state: AgentState) -> AgentState:
    """
    Hybrid classifier: Rule-based for clear cases, AI for ambiguous cases.

    Classification priority:
    0. dashboard_load - interaction_type is "dashboard_load" (deterministic)
    1. hardcoded - Exact match in hardcoded questions dictionary
    2. asin_product - ASIN param exists OR question contains "ASIN"/"ASINs"
    3. insight_query - compare_date_start exists OR question contains insight keywords
    4. metrics_query vs other_query - AI decides (business question vs general question)
    """
    
    question = state.get("question", "")
    logger.info(f"Classifying: '{question}'")
    
    # 0. Check for dashboard_load interaction type (deterministic, no AI needed)
    if state.get("interaction_type") == "dashboard_load":
        logger.info("Detected dashboard_load interaction type")
        state["question_type"] = "dashboard_load"
        return state
    
    # 1. Check hardcoded (exact match)
    if _is_hardcoded(question):
        question_type = "hardcoded"
        logger.info(f"Classified as hardcoded (exact match)")
        state["question_type"] = question_type
        return state
    
    # 2. Check ASIN query
    if _is_asin_query(question, state):
        question_type = "asin_product"
        logger.info(f"Classified as asin_product (ASIN detected)")
        state["question_type"] = question_type
        return state
    
    # 3. Check insight query
    if state.get("compare_date_start") or _has_insight_keywords(question):
        question_type = "insight_query"
        logger.info(f"Classified as insight_query (insight/comparison detected)")
        state["question_type"] = question_type
        return state
    
    # 4. AI decides: metrics_query vs other_query
    question_type = _classify_metrics_vs_other(question)
    logger.info(f"Classified as {question_type} (AI decision)")
    state["question_type"] = question_type
    
    return state
