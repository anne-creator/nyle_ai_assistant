"""
Simple Metrics Tool - Deterministic metric retrieval from Nyle backend APIs.

This tool:
1. Receives a list of metric names
2. Maps metrics to their corresponding API endpoints
3. Calls only the required endpoints (in parallel)
4. Returns only the requested metrics in a structured format
"""

import asyncio
from datetime import date, timedelta
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Set
import logging
import json

from app.metricsAccessLayer import metrics_api

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


# Mapping of metrics to their source endpoints (can have multiple endpoints per metric)
# Format: metric_name -> list of endpoints to try (in order of preference)
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
    "lost_sales": ["total", "cfo"],  # exists in both
    
    # CFO endpoint metrics
    "available_capital": ["cfo"],
    "frozen_capital": ["cfo"],
    "borrowed_capital": ["cfo"],
    "cost_of_goods_sold": ["cfo"],
    "gross_profit": ["cfo"],
    "net_profit": ["cfo"],
    "amazon_fees": ["cfo"],
    "misc": ["cfo"],
    "net_margin": ["cfo"],
    "opex": ["cfo"],
    "ebitda": ["cfo"],
    "roi": ["cfo"],  # moved from total to cfo only
    "contribution_margin": ["cfo"],  # moved from total to cfo only
    "contribution_profit": ["cfo"],  # moved from total to cfo only
    "gross_margin": ["cfo"],  # moved from total to cfo only
    
    # Organic endpoint metrics
    "organic_impressions": ["organic"],
    "organic_clicks": ["organic"],
    "organic_orders": ["organic"],
    "organic_units_sold": ["organic"],
    "organic_cvr": ["organic"],
    "organic_ctr": ["organic"],
    "organic_sales": ["organic"],
    "organic_lost_sales": ["organic"],
    "organic_add_to_cart": ["organic"],
    
    # Attribution endpoint metrics
    "attribution_sales": ["attribution"],
    "attribution_spend": ["attribution"],
    "attribution_impressions": ["attribution"],
    "attribution_clicks": ["attribution"],
    "attribution_units_sold": ["attribution"],
    "attribution_orders": ["attribution"],
    "attribution_ctr": ["attribution"],
    "attribution_cvr": ["attribution"],
    "attribution_acos": ["attribution"],
    "attribution_roas": ["attribution"],
    "attribution_cpc": ["attribution"],
    "attribution_cpm": ["attribution"],
    "attribution_add_to_cart": ["attribution"],
    
    # Inventory endpoint metrics
    "safety_stock": ["inventory"],
    "inventory_turnover": ["inventory"],
    "fba_in_stock_rate": ["inventory"],
}


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


def build_lowercase_key_map(response_data) -> Dict[str, Any]:
    """
    Build a lowercase key -> value mapping from API response.
    Handles multiple response formats:
    - {"data": [{"value": {...metrics...}}]} (timespan=day format)
    - [{"metric": value}] (plain list)
    - {"data": {...metrics...}} (nested dict)
    - {"metric": value} (flat dict)
    """
    # Handle list response directly
    if isinstance(response_data, list):
        if len(response_data) > 0 and isinstance(response_data[0], dict):
            first_item = response_data[0]
            # Check if metrics are in 'value' key
            if 'value' in first_item and isinstance(first_item['value'], dict):
                return {normalize_metric_name(k): v for k, v in first_item['value'].items()}
            return {normalize_metric_name(k): v for k, v in first_item.items()}
        return {}
    
    # Handle dict response
    if isinstance(response_data, dict):
        # Check if 'data' is a list (timespan=day format: {"data": [{"value": {...}}]})
        if 'data' in response_data and isinstance(response_data['data'], list):
            data_list = response_data['data']
            if len(data_list) > 0 and isinstance(data_list[0], dict):
                first_item = data_list[0]
                # Check if metrics are in 'value' key
                if 'value' in first_item and isinstance(first_item['value'], dict):
                    return {normalize_metric_name(k): v for k, v in first_item['value'].items()}
                return {normalize_metric_name(k): v for k, v in first_item.items()}
            return {}
        
        # Check if 'data' is a dict
        if 'data' in response_data and isinstance(response_data['data'], dict):
            return {normalize_metric_name(k): v for k, v in response_data['data'].items()}
        
        # Metrics at top level
        return {normalize_metric_name(k): v for k, v in response_data.items()}
    
    return {}


class MetricsInput(BaseModel):
    """Input schema for the simple metrics tool."""
    metric_list: List[str] = Field(description="List of metric names to retrieve (e.g., ['acos', 'total_sales', 'net_profit'])")
    date_start: str = Field(description="Start date in YYYY-MM-DD format")
    date_end: str = Field(description="End date in YYYY-MM-DD format")


class MetricsOutput(BaseModel):
    """Output schema for the simple metrics tool."""
    metrics: Dict[str, Any] = Field(description="Dictionary of requested metrics with their values")
    status: str = Field(description="Status of the operation (success/error)")
    message: str = Field(default="", description="Optional message about the operation")


@tool(args_schema=MetricsInput, return_direct=False)
async def get_simple_metrics(metric_list: List[str], date_start: str, date_end: str) -> str:
    """
    Retrieve specific metrics from Nyle backend APIs.
    
    This tool determines which API endpoints to call based on the requested metrics,
    fetches the data, and returns only the requested metrics in a structured JSON format.
    
    Args:
        metric_list: List of metric names to retrieve (e.g., ['acos', 'total_sales', 'net_profit'])
        date_start: Start date in YYYY-MM-DD format
        date_end: End date in YYYY-MM-DD format
        
    Returns:
        JSON string containing only the requested metrics with their values
    """
    logger.info(f"Simple Metrics Tool called with metrics: {metric_list}, dates: {date_start} to {date_end}")
    
    # Check if this is a forecasted query (today or yesterday single day)
    is_forecasted = is_forecasted_query(date_start, date_end)
    timespan = "day" if is_forecasted else None
    logger.info(f"Is forecasted query: {is_forecasted}, timespan: {timespan}")
    
    try:
        # Step 1: Determine ALL endpoints needed (including fallbacks)
        endpoints_needed: Set[str] = set()
        for metric in metric_list:
            metric_normalized = normalize_metric_name(metric)
            if metric_normalized in METRIC_TO_ENDPOINTS:
                # Add all possible endpoints for this metric
                endpoints_needed.update(METRIC_TO_ENDPOINTS[metric_normalized])
            else:
                logger.warning(f"Unknown metric: {metric}")
        
        logger.info(f"Endpoints needed: {endpoints_needed}")
        
        # Step 2: Call all required endpoints in parallel
        api_tasks = {}
        
        if "ads" in endpoints_needed:
            api_tasks["ads"] = metrics_api.get_ads_executive_summary(date_start, date_end, timespan=timespan)
        if "total" in endpoints_needed:
            api_tasks["total"] = metrics_api.get_total_metrics_summary(date_start, date_end, timespan=timespan)
        if "cfo" in endpoints_needed:
            api_tasks["cfo"] = metrics_api.get_financial_summary(date_start, date_end, timespan=timespan)
        if "organic" in endpoints_needed:
            api_tasks["organic"] = metrics_api.get_organic_metrics(date_start, date_end, timespan=timespan)
        if "attribution" in endpoints_needed:
            api_tasks["attribution"] = metrics_api.get_attribution_metrics(date_start, date_end, timespan=timespan)
        if "inventory" in endpoints_needed:
            api_tasks["inventory"] = metrics_api.get_inventory_status(date_start, date_end, timespan=timespan)
        
        # Execute all API calls in parallel
        api_responses: Dict[str, dict] = {}
        api_responses_normalized: Dict[str, Dict[str, Any]] = {}  # lowercase key maps
        
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
                    # Build normalized map and log
                    normalized = build_lowercase_key_map(result)
                    normalized_keys = list(normalized.keys())[:10]
                    logger.info(f"Retrieved {key} data - extracted {len(normalized)} metrics: {normalized_keys}")
                    api_responses[key] = result
                    api_responses_normalized[key] = normalized
        
        # Step 3: Extract requested metrics (try all endpoints for each metric)
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
                # Log available keys from all tried endpoints
                all_available_keys = []
                for endpoint in endpoints_to_try:
                    if endpoint in api_responses_normalized:
                        all_available_keys.extend(list(api_responses_normalized[endpoint].keys()))
                logger.warning(f"Metric {metric} not found. Tried endpoints: {endpoints_to_try}. Available keys: {all_available_keys}")
        
        # Step 4: Truncate decimals and return structured JSON
        result_metrics = truncate_decimals(result_metrics)
        output = {
            "status": "success",
            "metrics": result_metrics,
            "message": f"Successfully retrieved {len(result_metrics)} metrics",
            "is_forecasted": is_forecasted
        }
        
        logger.info(f"Returning metrics: {result_metrics}, is_forecasted: {is_forecasted}")
        return json.dumps(output)
    
    except Exception as e:
        logger.error(f"Error in simple metrics tool: {str(e)}", exc_info=True)
        output = {
            "status": "error",
            "metrics": {},
            "message": f"Error retrieving metrics: {str(e)}",
            "is_forecasted": False
        }
        return json.dumps(output)
