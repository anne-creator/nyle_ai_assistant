import logging
from datetime import datetime, timedelta

from langchain_openai import ChatOpenAI

from app.models.agentState import AgentState
from app.config import get_settings
from app.metricsAccessLayer import metrics_api
from app.context import set_jwt_token_for_task
from app.graph.nodes.insight_query_handler.prompt import (
    INSIGHT_INTENT_PROMPT,
    COMPARISON_EXPLANATION_PROMPT,
    TREND_ANALYSIS_PROMPT
)
from app.utils.trend_metrics_fetcher import fetch_trend_metrics

logger = logging.getLogger(__name__)


def _classify_insight_intent(question: str) -> str:
    """Sub-classify the insight intent using LLM."""
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key,
        streaming=True
    )
    
    prompt = INSIGHT_INTENT_PROMPT.format(question=question)
    response = llm.invoke(prompt)
    intent = response.content.strip().lower()
    
    # Validate intent
    if intent not in ["net_profit_loss", "comparison", "trend_analysis"]:
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
    3. get_ads_executive_summary() for period A (Ad TOS IS)
    4. get_ads_executive_summary() for period B (Ad TOS IS)
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
    
    # Extract Ad TOS IS (Top of Search Impression Share) from ads data
    tos_is_a = ads_a.get("tos_is", ads_a.get("TOS_IS", ads_a.get("top_of_search_is", 0)))
    tos_is_b = ads_b.get("tos_is", ads_b.get("TOS_IS", ads_b.get("top_of_search_is", 0)))
    
    return {
        "period_a_start": date_start,
        "period_a_end": date_end,
        "period_b_start": compare_start,
        "period_b_end": compare_end,
        "non_optimal_a": non_optimal_a,
        "non_optimal_b": non_optimal_b,
        "tos_is_a": tos_is_a,
        "tos_is_b": tos_is_b,
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


def _format_date_range(start_str: str, end_str: str) -> str:
    """
    Format date range like metrics_query_handler: (Sep 1-14, 2025)
    - Same month: "Sep 1-14, 2025"
    - Different months: "Sep 1 - Oct 14, 2025"
    - Single day: "Sep 1, 2025"
    """
    start = datetime.strptime(start_str, "%Y-%m-%d")
    end = datetime.strptime(end_str, "%Y-%m-%d")
    
    if start == end:
        # Single day: "Sep 1, 2025"
        return start.strftime("%b %-d, %Y")
    elif start.month == end.month and start.year == end.year:
        # Same month: "Sep 1-14, 2025"
        return f"{start.strftime('%b')} {start.day}-{end.day}, {start.year}"
    elif start.year == end.year:
        # Different months, same year: "Sep 1 - Oct 14, 2025"
        return f"{start.strftime('%b')} {start.day} - {end.strftime('%b')} {end.day}, {start.year}"
    else:
        # Different years: "Dec 15, 2024 - Jan 14, 2025"
        return f"{start.strftime('%b')} {start.day}, {start.year} - {end.strftime('%b')} {end.day}, {end.year}"


def _format_net_profit_response(data: dict) -> str:
    """
    Deterministic formatting for net profit loss response.
    No LLM needed - uses fixed template with metric values.
    """
    non_optimal_a = data["non_optimal_a"]
    tos_is_a = data["tos_is_a"]
    tos_is_b = data["tos_is_b"]
    
    # Format date ranges for readability (Sep 1-14, 2025 format)
    period_a = _format_date_range(data["period_a_start"], data["period_a_end"])
    period_b = _format_date_range(data["period_b_start"], data["period_b_end"])
    
    return (
        f"Your net profit loss due to non-optimal spend over {period_a} "
        f"was ${non_optimal_a:,.2f}, because you set your goal:\n"
        f"- Ad TOS IS as {tos_is_a}% at {period_a} "
        f"vs Ad TOS IS as {tos_is_b}% at {period_b}"
    )


def _generate_comparison_explanation(data: dict, question: str) -> str:
    """Generate LLM explanation for comparison data."""
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.3,
        api_key=settings.openai_api_key,
        streaming=True
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


def _generate_trend_analysis_response(data: dict, question: str) -> str:
    """
    Generate LLM analysis for trend data.
    
    Uses TREND_ANALYSIS_PROMPT to identify trends in net profit,
    correlate with other metrics, and explain root causes.
    """
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.3,
        api_key=settings.openai_api_key,
        streaming=True
    )
    
    prompt = f"""{TREND_ANALYSIS_PROMPT}

**Daily Metrics Data:**
{data['text']}

**Summary Statistics:**
- Net Profit: Sum=${data['stats']['profit']['sum']:,}, Avg=${data['stats']['profit']['avg']:,}, Max=${data['stats']['profit']['max']:,}, Min=${data['stats']['profit']['min']:,}
- Total Sales: Sum=${data['stats']['sales']['sum']:,}, Avg=${data['stats']['sales']['avg']:,}
- ACOS Avg: {data['stats']['acos_avg']}%
- TOS IS Avg: {data['stats']['tos_avg']}%
- ROI Avg: {data['stats']['roi_avg']}%

**User Question:** {question}

**Analysis:**"""
    
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
        response = _format_net_profit_response(data)
    elif insight_intent == "trend_analysis":
        # Use reusable trend metrics fetcher tool
        asin = state.get("asin")
        data = await fetch_trend_metrics(
            state["date_start"],
            state["date_end"],
            timespan="day",
            asin=asin
        )
        response = _generate_trend_analysis_response(data, question)
    else:  # comparison
        data = await _execute_comparison_pipeline(state)
        response = _generate_comparison_explanation(data, question)
    
    # 3. Set response
    state["response"] = response
    logger.info("Generated insight response")
    
    return state

