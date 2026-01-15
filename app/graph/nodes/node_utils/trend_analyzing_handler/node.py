"""
Trend Analyzing Handler Node - Reusable node for trend analysis queries.

This node:
- Fetches daily metrics for a time period
- Generates LLM-powered trend analysis
- Provides optimization recommendations
- Can be used by any handler that needs trend analysis

Handles questions like:
- "Give me insights from Oct 1 to Oct 30"
- "What happened last month?"
- "Show me trends for last week"
"""

import logging
from datetime import datetime, timedelta

from langchain_openai import ChatOpenAI

from app.models.agentState import AgentState
from app.config import get_settings
from app.metricsAccessLayer import metrics_api
from app.utils.trend_metrics_fetcher import fetch_trend_metrics
from app.utils.button_helpers import create_set_goal_button
from app.graph.nodes.classifier_route_node.insight_query_handler.prompt import (
    TREND_ANALYSIS_PROMPT
)

logger = logging.getLogger(__name__)


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


def _calculate_next_period(date_end: str) -> tuple[str, str]:
    """
    Calculate the next recommended goal period.
    Starts the day after analysis period ends, with a 15-day window.
    """
    end = datetime.strptime(date_end, "%Y-%m-%d")
    next_start = end + timedelta(days=1)
    next_end = next_start + timedelta(days=14)  # 15-day window
    return next_start.strftime("%Y-%m-%d"), next_end.strftime("%Y-%m-%d")


def _generate_trend_analysis_response(data: dict, question: str) -> str:
    """
    Generate LLM analysis for trend data.
    
    Uses TREND_ANALYSIS_PROMPT to identify trends in net profit,
    correlate with other metrics, and explain root causes.
    """
    # Check if we have any data
    if not data.get('stats') or data.get('days', 0) == 0:
        return f"No data available for the requested period. {data.get('text', '')}"
    
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.3,
        api_key=settings.openai_api_key,
        streaming=True
    )
    
    # Build summary statistics only if stats exist
    stats = data.get('stats', {})
    profit_stats = stats.get('profit', {})
    sales_stats = stats.get('sales', {})
    
    prompt = f"""{TREND_ANALYSIS_PROMPT}

**Daily Metrics Data:**
{data['text']}

**Summary Statistics:**
- Net Profit: Sum=${profit_stats.get('sum', 0):,}, Avg=${profit_stats.get('avg', 0):,}, Max=${profit_stats.get('max', 0):,}, Min=${profit_stats.get('min', 0):,}
- Total Sales: Sum=${sales_stats.get('sum', 0):,}, Avg=${sales_stats.get('avg', 0):,}
- ACOS Avg: {stats.get('acos_avg', 0):.2f}%
- Ad TOS IS Avg: {stats.get('ad_tos_is_avg', 0):.2f}%
- ROI Avg: {stats.get('roi_avg', 0):.2f}%

**User Question:** {question}

**Analysis:**"""
    
    response = llm.invoke(prompt)
    return response.content.strip()


async def _get_optimization_potential(
    date_start: str, 
    date_end: str, 
    asin: str = None
) -> str:
    """
    Get optimization potential by calling optimal_goals API.
    
    Returns formatted text with ACOS recommendation only.
    Provides forward-looking goal suggestion for the next period.
    """
    try:
        # Fetch optimal goals
        optimal = await metrics_api.get_optimal_goals(date_start, date_end, asin=asin)
        
        if not isinstance(optimal, dict):
            logger.warning(f"Invalid optimal_goals response: {optimal}")
            return ""
        
        # Extract ACOS value only
        acos_value = optimal.get("acos")
        
        # Skip if ACOS is None or 0
        if acos_value is None or acos_value == 0:
            return ""
        
        # Calculate the next period for recommendations
        next_start, next_end = _calculate_next_period(date_end)
        next_period_range = _format_date_range(next_start, next_end)
        
        # Round ACOS to whole number for display and button
        acos_rounded = round(acos_value)
        acos_formatted = f"{acos_rounded}%"
        
        # Create the set_goal button with ACOS and next period dates
        button_markup = create_set_goal_button(
            metric_name="acos",
            metric_value=acos_rounded,
            date_start=next_start,
            date_end=next_end
        )
        
        # Build the forward-looking recommendation text with button
        optimization_text = (
            f"Looking ahead, I want to help you stabilize your business performance. "
            f"Based on scenario simulations combining your historical data patterns with predictive modeling.\n\n"
            f"Recommended goals ({next_period_range}):\n"
            f"ACOS: {acos_formatted}\n\n"
            f"Would you like me to update this goal for you?\n\n"
            f"{button_markup}"
        )
        
        return optimization_text
        
    except Exception as e:
        logger.warning(f"Error getting optimization potential: {e}")
        return ""


async def trend_analyzing_handler_node(state: AgentState) -> dict:
    """
    Reusable node for trend analysis queries.
    
    This node:
    1. Extracts date_start, date_end, asin, question from state
    2. Fetches daily metrics using fetch_trend_metrics()
    3. Generates LLM-powered trend analysis
    4. Fetches optimization recommendations
    5. Combines all parts into a complete response
    
    Handles questions like:
    - "Give me insights from Oct 1 to Oct 30"
    - "What happened last month?"
    - "Show me trends for last week"
    
    Args:
        state: AgentState with date_start, date_end, optional asin, and question
    
    Returns:
        dict with:
        - response: str - Complete formatted response with trends + optimization
    """
    date_start = state["date_start"]
    date_end = state["date_end"]
    asin = state.get("asin")
    question = state["question"]
    
    logger.info(f"Trend analyzing handler: {date_start} to {date_end}, asin={asin}")
    
    # Fetch daily metrics data
    data = await fetch_trend_metrics(
        date_start,
        date_end,
        timespan="day",
        asin=asin
    )
    
    # Generate trend analysis from LLM
    trend_response = _generate_trend_analysis_response(data, question)
    
    # Fetch optimization potential data
    optimization_text = await _get_optimization_potential(date_start, date_end, asin)
    
    # Combine trend analysis + optimization potential
    response = trend_response + "\n\n" + optimization_text
    
    logger.info("Generated trend analysis response")
    
    return {"response": response}
