"""
Trend Metrics Fetcher - Reusable tool to fetch daily metrics for trend analysis.

Fetches 3 core KPIs + user goals in parallel and formats compactly for LLM consumption:
- ACOS, Ad TOS IS, Net Profit
- User-set goals for the period

Usage:
    from app.utils.trend_metrics_fetcher import fetch_trend_metrics
    
    data = await fetch_trend_metrics("2025-10-01", "2025-10-30")
"""

import asyncio
import logging
from typing import Optional

from app.metricsAccessLayer import metrics_api

logger = logging.getLogger(__name__)


async def fetch_trend_metrics(
    date_start: str,
    date_end: str,
    timespan: str = "day",
    asin: Optional[str] = None
) -> dict:
    """
    Fetch 3 core daily metrics + user goals in parallel and format for LLM consumption.
    
    Args:
        date_start: Start date (YYYY-MM-DD)
        date_end: End date (YYYY-MM-DD)
        timespan: Time granularity (default: "day")
        asin: Optional ASIN filter
    
    Returns:
        Compact format for LLM:
        {
            "period": "2025-10-01 to 2025-10-30",
            "days": 30,
            "data": [{"d": "2025-10-01", "acos": 12.5, "ad_tos_is": 45.2, "profit": 3200}, ...],
            "stats": {"profit": {"sum": ..., "avg": ..., "max": ..., "min": ...}, "acos_avg": ..., "ad_tos_is_avg": ...},
            "goals": [{"asin": "...", "metric": "acos", "value": 23, ...}],
            "goals_text": "User-Set Goals:\n- ACOS: 23% (2025-10-01 to 2025-10-15)...",
            "text": "Daily Metrics 2025-10-01 to 2025-10-30:\ndate|ACOS|Ad_TOS_IS|Profit\n2025-10-01|12.5%|45.2%|$3,200\n..."
        }
    """
    logger.info(f"Fetching trend metrics: {date_start} to {date_end}")
    
    # Fetch 3 core metrics + goals in parallel
    acos_data, tos_data, profit_data, goals_data = await asyncio.gather(
        metrics_api.get_daily_acos(date_start, date_end, timespan, asin),
        metrics_api.get_daily_ad_tos_is(date_start, date_end, timespan, asin),
        metrics_api.get_daily_net_profit(date_start, date_end, timespan, asin),
        metrics_api.get_goals_list(date_start, date_end, asin),
        return_exceptions=True
    )
    
    # Extract data arrays (handle errors gracefully)
    acos_list = _extract_data(acos_data)
    tos_list = _extract_data(tos_data)
    profit_list = _extract_data(profit_data)
    
    # Use the longest list to determine days
    max_len = max(len(acos_list), len(tos_list), len(profit_list))
    
    if max_len == 0:
        return {
            "period": f"{date_start} to {date_end}",
            "days": 0,
            "data": [],
            "stats": {},
            "goals": [],
            "goals_text": "No active goals during this period.",
            "text": f"No data available for {date_start} to {date_end}"
        }
    
    # Build compact daily records
    # Note: ACOS comes as percentage (26.43 = 26.43%), no conversion needed
    # Note: Ad TOS IS comes as decimal (0.0459 = 4.59%), needs *100
    days = []
    for i in range(max_len):
        day_record = {
            "d": _get_date(profit_list, acos_list, tos_list, i),
            "acos": _get_value(acos_list, i, decimal_places=2),  # Already %
            "ad_tos_is": _get_value(tos_list, i, multiply_100=True, decimal_places=2),  # Decimal → %
            "profit": _get_value(profit_list, i, round_int=True)
        }
        days.append(day_record)
    
    # Calculate summary stats
    stats = _calculate_stats(days)
    
    # Build compact text for LLM (token-efficient)
    # Format: date|acos%|ad_tos_is%|$profit
    lines = [
        f"{d['d']}|{d['acos']:.2f}%|{d['ad_tos_is']:.2f}%|${d['profit']:,}"
        for d in days
    ]
    text = f"Daily Metrics {date_start} to {date_end} ({len(days)} days):\n"
    text += "date|ACOS|Ad_TOS_IS|Profit\n"
    text += "\n".join(lines)
    
    # Format goals for LLM
    goals_list = _extract_goals(goals_data)
    goals_text = _format_goals_for_llm(goals_list)
    
    return {
        "period": f"{date_start} to {date_end}",
        "days": len(days),
        "data": days,
        "stats": stats,
        "goals": goals_list,
        "goals_text": goals_text,
        "text": text
    }


def _extract_data(response) -> list:
    """Extract data array from API response, handling errors."""
    if isinstance(response, Exception):
        logger.warning(f"API error: {response}")
        return []
    if isinstance(response, dict):
        return response.get("data", [])
    return []


def _extract_goals(response) -> list:
    """Extract goals array from API response, handling errors."""
    if isinstance(response, Exception):
        logger.warning(f"Goals API error: {response}")
        return []
    if isinstance(response, dict):
        return response.get("goals", [])
    return []


def _get_date(profit_list, acos_list, tos_list, index) -> str:
    """Get date from any available data source at given index."""
    for data_list in [profit_list, acos_list, tos_list]:
        if index < len(data_list) and data_list[index]:
            period_start = data_list[index].get("period_start", "")
            if period_start:
                return period_start[:10]  # date only, no time
    return ""


def _get_value(
    data_list: list, 
    index: int, 
    multiply_100: bool = False, 
    round_int: bool = False,
    decimal_places: int = 2
) -> float:
    """
    Safely extract value from data list at index.
    
    Args:
        data_list: List of data points from API
        index: Index to extract
        multiply_100: True for values that are decimals needing *100 (e.g., 0.0459 → 4.59%)
        round_int: True to return as integer
        decimal_places: Number of decimal places for rounding
    """
    if index >= len(data_list) or not data_list[index]:
        return 0.0
    
    value = data_list[index].get("value", 0) or 0
    
    if multiply_100:
        value = value * 100
    if round_int:
        return int(round(value, 0))
    return round(value, decimal_places)


def _calculate_stats(days: list) -> dict:
    """Calculate summary statistics for each metric."""
    if not days:
        return {}
    
    profit_vals = [d["profit"] for d in days]
    acos_vals = [d["acos"] for d in days]
    ad_tos_is_vals = [d["ad_tos_is"] for d in days]
    
    return {
        "profit": {
            "sum": sum(profit_vals),
            "avg": sum(profit_vals) // len(profit_vals) if profit_vals else 0,
            "max": max(profit_vals) if profit_vals else 0,
            "min": min(profit_vals) if profit_vals else 0
        },
        "acos_avg": round(sum(acos_vals) / len(acos_vals), 2) if acos_vals else 0,
        "ad_tos_is_avg": round(sum(ad_tos_is_vals) / len(ad_tos_is_vals), 2) if ad_tos_is_vals else 0
    }


def _format_goals_for_llm(goals: list) -> str:
    """Format goals list for LLM consumption."""
    if not goals:
        return "No active goals during this period."
    
    lines = ["User-Set Goals:"]
    for g in goals:
        asin_label = g.get('asin', 'All Products')
        metric_name = g.get('metric', '').upper()
        value = g.get('value', 0)
        date_start = g.get('date_start', '')
        date_end = g.get('date_end', '')
        lines.append(f"- {metric_name}: {value}% ({date_start} to {date_end}) [ASIN: {asin_label}]")
    return "\n".join(lines)

