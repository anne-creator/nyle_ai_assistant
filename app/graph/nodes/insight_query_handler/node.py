import logging
from datetime import datetime, timedelta

from langchain_openai import ChatOpenAI

from app.models.agentState import AgentState
from app.config import get_settings
from app.metricsAccessLayer import metrics_api
from app.context import set_jwt_token_for_task
from app.graph.nodes.insight_query_handler.prompt import (
    INSIGHT_INTENT_PROMPT,
    NET_PROFIT_LOSS_EXPLANATION_PROMPT,
    COMPARISON_EXPLANATION_PROMPT
)

logger = logging.getLogger(__name__)


def _classify_insight_intent(question: str) -> str:
    """Sub-classify the insight intent using LLM."""
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key
    )
    
    prompt = INSIGHT_INTENT_PROMPT.format(question=question)
    response = llm.invoke(prompt)
    intent = response.content.strip().lower()
    
    # Validate intent
    if intent not in ["net_profit_loss", "comparison"]:
        logger.warning(f"Invalid insight intent '{intent}', defaulting to comparison")
        intent = "comparison"
    
    return intent


def _derive_comparison_period(date_start: str, date_end: str) -> tuple[str, str]:
    """Derive the previous same-length period for comparison."""
    start = datetime.strptime(date_start, "%Y-%m-%d")
    end = datetime.strptime(date_end, "%Y-%m-%d")
    period_length = (end - start).days + 1
    
    # Previous period ends the day before current period starts
    compare_end = start - timedelta(days=1)
    compare_start = compare_end - timedelta(days=period_length - 1)
    
    return compare_start.strftime("%Y-%m-%d"), compare_end.strftime("%Y-%m-%d")


async def _execute_net_profit_loss_pipeline(state: AgentState) -> dict:
    """
    Deterministic pipeline for net profit loss questions.
    
    Calls:
    1. get_non_optimal_spends() for period A
    2. get_non_optimal_spends() for period B (derived if not provided)
    3. get_ads_executive_summary() for period A (TACoS)
    4. get_ads_executive_summary() for period B (TACoS)
    """
    date_start = state["date_start"]
    date_end = state["date_end"]
    
    # Derive comparison period if not provided
    if state.get("compare_date_start") and state.get("compare_date_end"):
        compare_start = state["compare_date_start"]
        compare_end = state["compare_date_end"]
    else:
        compare_start, compare_end = _derive_comparison_period(date_start, date_end)
    
    logger.info(f"Net profit loss pipeline: A=[{date_start} to {date_end}], B=[{compare_start} to {compare_end}]")
    
    # Call APIs for period A
    non_optimal_a = await metrics_api.get_non_optimal_spends(date_start, date_end)
    ads_a = await metrics_api.get_ads_executive_summary(date_start, date_end)
    
    # Call APIs for period B
    non_optimal_b = await metrics_api.get_non_optimal_spends(compare_start, compare_end)
    ads_b = await metrics_api.get_ads_executive_summary(compare_start, compare_end)
    
    # Extract TACoS from ads data (handle different possible response structures)
    tacos_a = ads_a.get("tacos", ads_a.get("TACoS", 0))
    tacos_b = ads_b.get("tacos", ads_b.get("TACoS", 0))
    
    # Calculate delta
    delta = non_optimal_a - non_optimal_b
    
    return {
        "period_a_start": date_start,
        "period_a_end": date_end,
        "period_b_start": compare_start,
        "period_b_end": compare_end,
        "non_optimal_a": non_optimal_a,
        "non_optimal_b": non_optimal_b,
        "delta": delta,
        "tacos_a": tacos_a,
        "tacos_b": tacos_b,
    }


async def _execute_comparison_pipeline(state: AgentState) -> dict:
    """
    Deterministic pipeline for general comparison questions.
    
    Calls ads executive summary for both periods.
    """
    date_start = state["date_start"]
    date_end = state["date_end"]
    
    # Derive comparison period if not provided
    if state.get("compare_date_start") and state.get("compare_date_end"):
        compare_start = state["compare_date_start"]
        compare_end = state["compare_date_end"]
    else:
        compare_start, compare_end = _derive_comparison_period(date_start, date_end)
    
    logger.info(f"Comparison pipeline: A=[{date_start} to {date_end}], B=[{compare_start} to {compare_end}]")
    
    # Fetch current period
    current = await metrics_api.get_ads_executive_summary(date_start, date_end)
    
    # Fetch comparison period
    comparison = await metrics_api.get_ads_executive_summary(compare_start, compare_end)
    
    return {
        "period_a_start": date_start,
        "period_a_end": date_end,
        "period_b_start": compare_start,
        "period_b_end": compare_end,
        "current": current,
        "comparison": comparison
    }


def _generate_net_profit_explanation(data: dict, question: str) -> str:
    """Generate LLM explanation for net profit loss data."""
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.3,
        api_key=settings.openai_api_key
    )
    
    prompt = NET_PROFIT_LOSS_EXPLANATION_PROMPT.format(
        period_a_start=data["period_a_start"],
        period_a_end=data["period_a_end"],
        period_b_start=data["period_b_start"],
        period_b_end=data["period_b_end"],
        non_optimal_a=data["non_optimal_a"],
        non_optimal_b=data["non_optimal_b"],
        delta=data["delta"],
        tacos_a=data["tacos_a"],
        tacos_b=data["tacos_b"],
        question=question
    )
    
    response = llm.invoke(prompt)
    return response.content.strip()


def _generate_comparison_explanation(data: dict, question: str) -> str:
    """Generate LLM explanation for comparison data."""
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.3,
        api_key=settings.openai_api_key
    )
    
    prompt = f"""{COMPARISON_EXPLANATION_PROMPT}

**Data:**
Current period ({data['period_a_start']} to {data['period_a_end']}):
{data['current']}

Comparison period ({data['period_b_start']} to {data['period_b_end']}):
{data['comparison']}

**User Question:** {question}

**Response:**"""
    
    response = llm.invoke(prompt)
    return response.content.strip()


async def insight_query_handler_node(state: AgentState) -> AgentState:
    """
    Handler for insight_query type questions.
    
    Handles questions like:
    - "What was my net profit losses over Oct 15 - Oct 30?"
    - "Compare August vs September"
    - "Why did my TACoS get worse?"
    """
    # Ensure JWT token is available for async tasks
    set_jwt_token_for_task(state["_jwt_token"])
    
    question = state["question"]
    logger.info(f"Processing insight_query: '{question}'")
    
    # 1. Sub-classify insight_intent
    insight_intent = _classify_insight_intent(question)
    state["insight_intent"] = insight_intent
    logger.info(f"Insight intent: {insight_intent}")
    
    # 2. Execute deterministic pipeline based on intent
    if insight_intent == "net_profit_loss":
        data = await _execute_net_profit_loss_pipeline(state)
        response = _generate_net_profit_explanation(data, question)
    else:  # comparison
        data = await _execute_comparison_pipeline(state)
        response = _generate_comparison_explanation(data, question)
    
    # 3. Set response
    state["response"] = response
    logger.info("Generated insight response")
    
    return state

