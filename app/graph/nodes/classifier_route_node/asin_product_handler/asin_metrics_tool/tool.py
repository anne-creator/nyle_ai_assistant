"""
ASIN Metrics Tool - Retrieval of ASIN-level metrics from Nyle backend APIs.

This tool provides:
1. get_ranked_products - Get top/bottom N products sorted by a metric (includes units & CVR)
2. get_asin_metrics - Get specific metrics for a single ASIN
"""

import asyncio
import json
import logging
from datetime import date, timedelta
from typing import List, Dict, Any, Set, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.metricsAccessLayer import metrics_api
from app.metricsAccessLayer.products_api import products_api

logger = logging.getLogger(__name__)


def is_forecasted_query(date_start: str, date_end: str) -> bool:
    """
    Check if query is for forecasted data.
    
    Forecasted = single day query for today or yesterday.
    Returns True if (date_start == date_end == today) or (date_start == date_end == yesterday)
    """
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    today_str = today.isoformat()
    yesterday_str = yesterday.isoformat()
    
    is_today = (date_start == today_str and date_end == today_str)
    is_yesterday = (date_start == yesterday_str and date_end == yesterday_str)
    
    return is_today or is_yesterday


# ========== Helper: Fetch Units and CVR for an ASIN ==========

def normalize_metric_name(name: str) -> str:
    """Normalize metric name to lowercase with underscores."""
    return name.lower().replace(" ", "_").replace("-", "_")


def truncate_decimals(value: Any) -> Any:
    """
    Truncate decimal numbers to integers (cut decimals, don't round).
    Handles floats, ints, dicts, and lists recursively.
    """
    if isinstance(value, float):
        return int(value)
    elif isinstance(value, dict):
        return {k: truncate_decimals(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [truncate_decimals(v) for v in value]
    return value


def build_lowercase_key_map(response_data: dict) -> Dict[str, Any]:
    """Build a lowercase key -> value mapping from API response."""
    return {normalize_metric_name(k): v for k, v in response_data.items()}


async def fetch_asin_net_profit_roi(asin: str, date_start: str, date_end: str, timespan: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch net_profit and roi for a specific ASIN from the cfo endpoint.
    
    Returns:
        Dict with 'net_profit' and 'roi' keys
    """
    try:
        result = await metrics_api.get_financial_summary(
            date_start, date_end, asin=asin, timespan=timespan
        )
        normalized = build_lowercase_key_map(result)
        return {
            "net_profit": normalized.get("net_profit", 0),
            "roi": normalized.get("roi", 0)
        }
    except Exception as e:
        logger.warning(f"Failed to fetch net_profit/roi for ASIN {asin}: {e}")
        return {"net_profit": 0, "roi": 0}


# ========== Tool 1: get_ranked_products ==========

# Map friendly names to API field names
ORDER_BY_MAP = {
    "total_sales": "executive_summary.total_sales",
    "net_profit": "executive_summary.net_profit",
    "gross_profit": "executive_summary.gross_profit",
    "roi": "executive_summary.roi",
    "gross_margin": "executive_summary.gross_margin",
    "contribution_margin": "executive_summary.contribution_margin",
}


class RankedProductsInput(BaseModel):
    """Input schema for the ranked products tool."""
    limit: int = Field(description="Number of products to return (e.g., 5 for 'top 5')")
    order_direction: int = Field(description="1=descending (top/best), 0=ascending (lowest/worst)")
    order_by: str = Field(
        default="total_sales",
        description="Field to sort by: total_sales, net_profit, gross_profit, roi, gross_margin"
    )
    date_start: str = Field(description="Start date in YYYY-MM-DD format for fetching net_profit/ROI")
    date_end: str = Field(description="End date in YYYY-MM-DD format for fetching net_profit/ROI")


@tool(args_schema=RankedProductsInput, return_direct=False)
async def get_ranked_products(
    limit: int,
    order_direction: int,
    date_start: str,
    date_end: str,
    order_by: str = "total_sales"
) -> str:
    """
    Get top/bottom N products sorted by a metric, including net profit and ROI.
    
    Steps:
    1. Get ranked products from /amazon/v1/products/own
    2. For each ASIN, fetch net_profit and roi from the cfo endpoint
    3. Combine and return all data
    
    Args:
        limit: Number of products to return (e.g., 5 for 'top 5')
        order_direction: 1=descending (top/best), 0=ascending (lowest/worst)
        order_by: Field to sort by (total_sales, net_profit, gross_profit, roi, gross_margin)
        date_start: Start date for fetching net_profit/ROI metrics
        date_end: End date for fetching net_profit/ROI metrics
        
    Returns:
        JSON string containing list of products with total_sales, net_profit, and roi
    """
    logger.info(f"get_ranked_products called: limit={limit}, order_direction={order_direction}, order_by={order_by}")
    
    # Check if this is a forecasted query (today or yesterday single day)
    is_forecasted = is_forecasted_query(date_start, date_end)
    timespan = "day" if is_forecasted else None
    logger.info(f"Is forecasted query: {is_forecasted}, timespan: {timespan}")
    
    try:
        # Step 1: Get ranked products (NO timespan for /v1/products/public)
        api_order_by = ORDER_BY_MAP.get(order_by, "executive_summary.total_sales")
        
        products = await products_api.get_ranked_products(
            offset=0,
            limit=limit,
            order_direction=order_direction,
            order_by=api_order_by
        )
        
        logger.info(f"Retrieved {len(products)} products")
        
        # Step 2: For each ASIN, fetch net_profit and roi in parallel (with timespan for math API)
        asin_list = [p.get("asin") for p in products if p.get("asin")]
        
        net_profit_roi_tasks = [
            fetch_asin_net_profit_roi(asin, date_start, date_end, timespan=timespan)
            for asin in asin_list
        ]
        net_profit_roi_results = await asyncio.gather(*net_profit_roi_tasks)
        
        # Create lookup map
        asin_to_net_profit_roi = dict(zip(asin_list, net_profit_roi_results))
        
        # Step 3: Combine data
        formatted_products = []
        for product in products:
            asin = product.get("asin")
            exec_summary = product.get("executive_summary", {})
            net_profit_roi = asin_to_net_profit_roi.get(asin, {"net_profit": 0, "roi": 0})
            
            formatted_products.append({
                "asin": asin,
                "total_sales": exec_summary.get("total_sales", 0),
                "net_profit": net_profit_roi["net_profit"],
                "roi": net_profit_roi["roi"],
            })
        
        # Truncate decimals before returning
        formatted_products = truncate_decimals(formatted_products)
        
        return json.dumps({
            "status": "success",
            "products": formatted_products,
            "count": len(formatted_products),
            "is_forecasted": is_forecasted
        })
        
    except Exception as e:
        logger.error(f"Error in get_ranked_products: {str(e)}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"Error retrieving ranked products: {str(e)}",
            "products": [],
            "is_forecasted": False
        })


# ========== Tool 2: get_asin_metrics ==========

# Mapping of metrics to their source endpoints
METRIC_TO_ENDPOINTS = {
    # Ads endpoint metrics (also available in cfo as fallback)
    "ad_sales": ["ads", "cfo"],
    "ad_spend": ["ads", "cfo"],
    "ad_clicks": ["ads", "cfo"],
    "ad_impressions": ["ads", "cfo"],
    "ad_units_sold": ["ads", "cfo"],
    "ad_orders": ["ads", "cfo"],
    "acos": ["ads", "cfo"],
    "roas": ["ads", "cfo"],
    "cpc": ["ads", "cfo"],
    "cpm": ["ads", "cfo"],
    "cac": ["ads"],
    "ad_ctr": ["ads", "cfo"],
    "ad_cvr": ["ads", "cfo"],
    "time_in_budget": ["ads", "cfo"],
    "ad_tos_is": ["ads", "cfo"],
    
    # Total endpoint metrics
    "total_sales": ["total"],
    "total_spend": ["total"],
    "total_impressions": ["total"],
    "ctr": ["total"],
    "total_clicks": ["total"],
    "cvr": ["total"],
    "total_orders": ["total"],
    "total_units_sold": ["total"],
    "total_ntb_orders": ["total"],
    "tacos": ["total"],
    "mer": ["total"],
    "lost_sales": ["total"],
    
    # CFO endpoint metrics
    "gross_profit": ["cfo"],
    "net_profit": ["cfo"],
    "amazon_fees": ["cfo"],
    "cost_of_goods_sold": ["cfo"],
    "gross_margin": ["cfo"],
    "contribution_margin": ["cfo"],
    "roi": ["cfo"],  # moved from total to cfo only
    
    # Inventory endpoint metrics (already supports ASIN)
    "safety_stock": ["inventory"],
    "inventory_turnover": ["inventory"],
    "fba_in_stock_rate": ["inventory"],
}


class ASINMetricsInput(BaseModel):
    """Input schema for the ASIN metrics tool."""
    metric_list: List[str] = Field(
        description="List of metric names to retrieve (e.g., ['total_sales', 'net_profit'])"
    )
    date_start: str = Field(description="Start date in YYYY-MM-DD format")
    date_end: str = Field(description="End date in YYYY-MM-DD format")
    asin: str = Field(description="ASIN identifier (e.g., B08XYZ123)")


@tool(args_schema=ASINMetricsInput, return_direct=False)
async def get_asin_metrics(
    metric_list: List[str],
    date_start: str,
    date_end: str,
    asin: str
) -> str:
    """
    Retrieve metrics for a specific ASIN from Nyle backend APIs.
    
    Similar to simple_metrics_tool but passes ASIN param to API calls.
    
    Args:
        metric_list: List of metric names to retrieve
        date_start: Start date in YYYY-MM-DD format
        date_end: End date in YYYY-MM-DD format
        asin: ASIN identifier
        
    Returns:
        JSON string containing the requested metrics
    """
    logger.info(f"get_asin_metrics called: metrics={metric_list}, asin={asin}, dates={date_start} to {date_end}")
    
    # Check if this is a forecasted query (today or yesterday single day)
    is_forecasted = is_forecasted_query(date_start, date_end)
    timespan = "day" if is_forecasted else None
    logger.info(f"Is forecasted query: {is_forecasted}, timespan: {timespan}")
    
    try:
        # Step 1: Determine endpoints needed
        endpoints_needed: Set[str] = set()
        for metric in metric_list:
            metric_normalized = normalize_metric_name(metric)
            if metric_normalized in METRIC_TO_ENDPOINTS:
                endpoints_needed.update(METRIC_TO_ENDPOINTS[metric_normalized])
            else:
                logger.warning(f"Unknown metric: {metric}")
        
        logger.info(f"Endpoints needed: {endpoints_needed}")
        
        # Step 2: Call required endpoints in parallel (with ASIN param where supported)
        api_tasks = {}
        
        if "ads" in endpoints_needed:
            api_tasks["ads"] = metrics_api.get_ads_executive_summary(
                date_start, date_end, asin=asin, timespan=timespan
            )
        if "total" in endpoints_needed:
            api_tasks["total"] = metrics_api.get_total_metrics_summary(
                date_start, date_end, asin=asin, timespan=timespan
            )
        if "cfo" in endpoints_needed:
            api_tasks["cfo"] = metrics_api.get_financial_summary(
                date_start, date_end, asin=asin, timespan=timespan
            )
        if "inventory" in endpoints_needed:
            api_tasks["inventory"] = metrics_api.get_inventory_status(
                date_start, date_end, asin=asin, timespan=timespan
            )
        
        # Execute all API calls in parallel
        api_responses: Dict[str, dict] = {}
        api_responses_normalized: Dict[str, Dict[str, Any]] = {}
        
        if api_tasks:
            task_keys = list(api_tasks.keys())
            task_values = list(api_tasks.values())
            results = await asyncio.gather(*task_values, return_exceptions=True)
            
            for key, result in zip(task_keys, results):
                if isinstance(result, Exception):
                    logger.error(f"Error calling {key} endpoint: {result}")
                    api_responses[key] = {}
                    api_responses_normalized[key] = {}
                else:
                    logger.info(f"Retrieved {key} data")
                    api_responses[key] = result
                    api_responses_normalized[key] = build_lowercase_key_map(result)
        
        # Step 3: Extract requested metrics
        result_metrics = {}
        for metric in metric_list:
            metric_normalized = normalize_metric_name(metric)
            endpoints_to_try = METRIC_TO_ENDPOINTS.get(metric_normalized, [])
            
            found = False
            for endpoint in endpoints_to_try:
                if endpoint in api_responses_normalized:
                    normalized_response = api_responses_normalized[endpoint]
                    if metric_normalized in normalized_response:
                        result_metrics[metric] = normalized_response[metric_normalized]
                        logger.info(f"Found {metric} in {endpoint} endpoint")
                        found = True
                        break
            
            if not found:
                logger.warning(f"Metric {metric} not found in any endpoint")
        
        # Step 4: Truncate decimals and return structured JSON
        result_metrics = truncate_decimals(result_metrics)
        output = {
            "status": "success",
            "asin": asin,
            "metrics": result_metrics,
            "date_range": f"{date_start} to {date_end}",
            "message": f"Successfully retrieved {len(result_metrics)} metrics for ASIN {asin}",
            "is_forecasted": is_forecasted
        }
        
        logger.info(f"Returning metrics: {result_metrics}, is_forecasted: {is_forecasted}")
        return json.dumps(output)
        
    except Exception as e:
        logger.error(f"Error in get_asin_metrics: {str(e)}", exc_info=True)
        return json.dumps({
            "status": "error",
            "asin": asin,
            "metrics": {},
            "message": f"Error retrieving metrics: {str(e)}",
            "is_forecasted": False
        })

