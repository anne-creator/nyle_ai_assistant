"""
Simple Metrics Tool - Deterministic metric retrieval from Nyle backend APIs.

This tool:
1. Receives a list of metric names
2. Maps metrics to their corresponding API endpoints
3. Calls only the required endpoints (in parallel)
4. Returns only the requested metrics in a structured format
"""

import asyncio
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Set
import logging
import json

from app.metricsAccessLayer import metrics_api

logger = logging.getLogger(__name__)


# Mapping of metrics to their source endpoints (can have multiple endpoints per metric)
# Format: metric_name -> list of endpoints to try (in order of preference)
METRIC_TO_ENDPOINTS = {
    # Ads endpoint metrics
    "ad_sales": ["ads"],
    "ad_spend": ["ads"],
    "ad_clicks": ["ads"],
    "ad_impressions": ["ads"],
    "ad_units_sold": ["ads"],
    "ad_orders": ["ads"],
    "acos": ["ads"],
    "roas": ["ads"],
    "cpc": ["ads"],
    "cac": ["ads"],
    "ad_ctr": ["ads"],
    "ad_cvr": ["ads"],
    "time_in_budget": ["ads"],
    
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


def build_lowercase_key_map(response_data: dict) -> Dict[str, Any]:
    """Build a lowercase key -> value mapping from API response."""
    return {normalize_metric_name(k): v for k, v in response_data.items()}


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
            api_tasks["ads"] = metrics_api.get_ads_executive_summary(date_start, date_end)
        if "total" in endpoints_needed:
            api_tasks["total"] = metrics_api.get_total_metrics_summary(date_start, date_end)
        if "cfo" in endpoints_needed:
            api_tasks["cfo"] = metrics_api.get_financial_summary(date_start, date_end)
        if "organic" in endpoints_needed:
            api_tasks["organic"] = metrics_api.get_organic_metrics(date_start, date_end)
        if "attribution" in endpoints_needed:
            api_tasks["attribution"] = metrics_api.get_attribution_metrics(date_start, date_end)
        if "inventory" in endpoints_needed:
            api_tasks["inventory"] = metrics_api.get_inventory_status(date_start, date_end)
        
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
                    logger.info(f"Retrieved {key} data with keys: {list(result.keys()) if isinstance(result, dict) else 'not a dict'}")
                    api_responses[key] = result
                    api_responses_normalized[key] = build_lowercase_key_map(result)
        
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
                    if endpoint in api_responses:
                        all_available_keys.extend(list(api_responses[endpoint].keys()))
                logger.warning(f"Metric {metric} not found. Tried endpoints: {endpoints_to_try}. Available keys: {all_available_keys}")
        
        # Step 4: Return structured JSON
        output = {
            "status": "success",
            "metrics": result_metrics,
            "message": f"Successfully retrieved {len(result_metrics)} metrics"
        }
        
        logger.info(f"Returning metrics: {result_metrics}")
        return json.dumps(output)
    
    except Exception as e:
        logger.error(f"Error in simple metrics tool: {str(e)}", exc_info=True)
        output = {
            "status": "error",
            "metrics": {},
            "message": f"Error retrieving metrics: {str(e)}"
        }
        return json.dumps(output)
