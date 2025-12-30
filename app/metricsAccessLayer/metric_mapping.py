"""
Metric Mapping Configuration

Maps simplified metric names to their corresponding API endpoints and field names.
This allows for simple metric retrieval without needing to know which API to call.
"""

from typing import Dict, Any, Optional
from enum import Enum


class MetricSource(Enum):
    """API endpoint sources for metrics"""
    ADS = "ads_executive_summary"
    TOTAL = "total_metrics_summary"
    ORGANIC = "organic_metrics"
    CFO = "financial_summary"


# Metric name to (source, field_name) mapping
METRIC_MAP: Dict[str, tuple[MetricSource, str]] = {
    # Ad metrics from /math/ads/executive-summary
    "ad_sales": (MetricSource.ADS, "ad_sales"),
    "ad_spend": (MetricSource.ADS, "ad_spend"),
    "ad_impressions": (MetricSource.ADS, "ad_impressions"),
    "ad_ctr": (MetricSource.ADS, "ad_ctr"),
    "ad_clicks": (MetricSource.ADS, "ad_clicks"),
    "ad_cvr": (MetricSource.ADS, "ad_cvr"),
    "ad_orders": (MetricSource.ADS, "ad_orders"),
    "ad_units_sold": (MetricSource.ADS, "ad_units_sold"),
    "acos": (MetricSource.ADS, "acos"),
    "roas": (MetricSource.ADS, "roas"),
    "cpc": (MetricSource.ADS, "cpc"),
    "cpm": (MetricSource.ADS, "cpm"),
    "time_in_budget": (MetricSource.ADS, "time_in_budget"),
    "ad_tos_is": (MetricSource.ADS, "ad_tos_is"),

    # Total metrics from /math/total/executive-summary
    "total_sales": (MetricSource.TOTAL, "total_sales"),
    "total_spend": (MetricSource.TOTAL, "total_spend"),
    "total_impressions": (MetricSource.TOTAL, "total_impressions"),
    "ctr": (MetricSource.TOTAL, "ctr"),
    "total_clicks": (MetricSource.TOTAL, "total_clicks"),
    "cvr": (MetricSource.TOTAL, "cvr"),
    "total_orders": (MetricSource.TOTAL, "total_orders"),
    "total_units_sold": (MetricSource.TOTAL, "total_units_sold"),
    "total_ntb_orders": (MetricSource.TOTAL, "total_ntb_orders"),
    "tacos": (MetricSource.TOTAL, "tacos"),
    "mer": (MetricSource.TOTAL, "mer"),
    "lost_sales": (MetricSource.TOTAL, "lost_sales"),

    # Organic metrics from /math/organic/executive-summary
    "organic_sales": (MetricSource.ORGANIC, "total_sales"),
    "organic_spend": (MetricSource.ORGANIC, "total_spend"),
    "organic_impressions": (MetricSource.ORGANIC, "total_impressions"),
    "organic_ctr": (MetricSource.ORGANIC, "ctr"),
    "organic_clicks": (MetricSource.ORGANIC, "total_clicks"),
    "organic_cvr": (MetricSource.ORGANIC, "cvr"),
    "organic_orders": (MetricSource.ORGANIC, "total_orders"),
    "organic_units_sold": (MetricSource.ORGANIC, "total_units_sold"),
    "organic_ntb_orders": (MetricSource.ORGANIC, "total_ntb_orders"),
    "organic_tacos": (MetricSource.ORGANIC, "tacos"),
    "organic_mer": (MetricSource.ORGANIC, "mer"),
    "organic_lost_sales": (MetricSource.ORGANIC, "lost_sales"),

    # CFO/Financial metrics from /math/cfo/executive-summary
    "available_capital": (MetricSource.CFO, "available_capital"),
    "frozen_capital": (MetricSource.CFO, "frozen_capital"),
    "borrowed_capital": (MetricSource.CFO, "borrowed_capital"),
    "gross_profit": (MetricSource.CFO, "gross_profit"),
    "gross_margin": (MetricSource.CFO, "gross_margin"),
    "contribution_profit": (MetricSource.CFO, "contribution_profit"),
    "contribution_margin": (MetricSource.CFO, "contribution_margin"),
    "net_profit": (MetricSource.CFO, "net_profit"),
    "net_margin": (MetricSource.CFO, "net_margin"),
    "opex": (MetricSource.CFO, "opex"),
    "roi": (MetricSource.CFO, "roi"),
    "cost_of_goods_sold": (MetricSource.CFO, "cost_of_goods_sold"),
    "cogs": (MetricSource.CFO, "cost_of_goods_sold"),  # Alias
    "amazon_fees": (MetricSource.CFO, "amazon_fees"),
}


# Reverse mapping: API endpoint -> list of metrics
API_METRICS: Dict[MetricSource, list[str]] = {
    MetricSource.ADS: [
        "ad_sales", "ad_spend", "ad_impressions", "ad_ctr", "ad_clicks",
        "ad_cvr", "ad_orders", "ad_units_sold", "acos", "roas",
        "cpc", "cpm", "time_in_budget", "ad_tos_is"
    ],
    MetricSource.TOTAL: [
        "total_sales", "total_spend", "total_impressions", "ctr", "total_clicks",
        "cvr", "total_orders", "total_units_sold", "total_ntb_orders",
        "tacos", "mer", "lost_sales"
    ],
    MetricSource.ORGANIC: [
        "total_sales", "total_spend", "total_impressions", "ctr", "total_clicks",
        "cvr", "total_orders", "total_units_sold", "total_ntb_orders",
        "tacos", "mer", "lost_sales"
    ],
    MetricSource.CFO: [
        "available_capital", "frozen_capital", "borrowed_capital",
        "gross_profit", "gross_margin", "contribution_profit",
        "contribution_margin", "net_profit", "net_margin",
        "opex", "roi", "cost_of_goods_sold", "amazon_fees"
    ]
}


def get_metric_source(metric_name: str) -> Optional[tuple[MetricSource, str]]:
    """
    Get the API source and field name for a given metric.

    Args:
        metric_name: The simplified metric name

    Returns:
        Tuple of (MetricSource, field_name) or None if not found
    """
    return METRIC_MAP.get(metric_name.lower())


def get_api_method_name(source: MetricSource) -> str:
    """
    Get the metrics_api method name for a given source.

    Args:
        source: The MetricSource enum value

    Returns:
        Method name as string (e.g., "get_ads_executive_summary")
    """
    method_map = {
        MetricSource.ADS: "get_ads_executive_summary",
        MetricSource.TOTAL: "get_total_metrics_summary",
        MetricSource.ORGANIC: "get_organic_metrics",
        MetricSource.CFO: "get_financial_summary"
    }
    return method_map[source]


def get_all_metrics_from_api(source: MetricSource) -> list[str]:
    """
    Get all metric field names available from a specific API.

    Args:
        source: The MetricSource enum value

    Returns:
        List of metric field names
    """
    return API_METRICS.get(source, [])
