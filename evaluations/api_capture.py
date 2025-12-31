"""
API Capture Layer for E2E Evaluation.

Tracks which Math Metrics API endpoints are called during each request.
Uses contextvars for per-request isolation.
"""
from contextvars import ContextVar
from typing import List, Optional
import functools

# Context variable to store endpoints called per request
_endpoints_called: ContextVar[List[str]] = ContextVar("endpoints_called", default=None)


def init_capture():
    """Initialize capture for a new request. Call before each graph execution."""
    _endpoints_called.set([])


def get_captured_endpoints() -> List[str]:
    """Get list of endpoints called in current request."""
    endpoints = _endpoints_called.get()
    return endpoints if endpoints is not None else []


def get_captured_endpoints_str() -> str:
    """Get comma-separated string of endpoints called."""
    return ",".join(get_captured_endpoints())


def record_endpoint(endpoint_name: str):
    """Record that an endpoint was called."""
    endpoints = _endpoints_called.get()
    if endpoints is not None and endpoint_name not in endpoints:
        endpoints.append(endpoint_name)


def wrap_metrics_api(metrics_api):
    """
    Wrap the metrics_api singleton to capture endpoint calls.
    
    This patches the methods to record which endpoints are called.
    """
    original_ads = metrics_api.get_ads_executive_summary
    original_financial = metrics_api.get_financial_summary
    original_organic = metrics_api.get_organic_metrics
    original_inventory = metrics_api.get_inventory_status
    original_attribution = metrics_api.get_attribution_metrics
    original_total = metrics_api.get_total_metrics_summary
    
    @functools.wraps(original_ads)
    async def wrapped_ads(*args, **kwargs):
        record_endpoint("ads")
        return await original_ads(*args, **kwargs)
    
    @functools.wraps(original_financial)
    async def wrapped_financial(*args, **kwargs):
        record_endpoint("cfo")
        return await original_financial(*args, **kwargs)
    
    @functools.wraps(original_organic)
    async def wrapped_organic(*args, **kwargs):
        record_endpoint("organic")
        return await original_organic(*args, **kwargs)
    
    @functools.wraps(original_inventory)
    async def wrapped_inventory(*args, **kwargs):
        record_endpoint("inventory")
        return await original_inventory(*args, **kwargs)
    
    @functools.wraps(original_attribution)
    async def wrapped_attribution(*args, **kwargs):
        record_endpoint("attribution")
        return await original_attribution(*args, **kwargs)
    
    @functools.wraps(original_total)
    async def wrapped_total(*args, **kwargs):
        record_endpoint("total")
        return await original_total(*args, **kwargs)
    
    # Patch the methods
    metrics_api.get_ads_executive_summary = wrapped_ads
    metrics_api.get_financial_summary = wrapped_financial
    metrics_api.get_organic_metrics = wrapped_organic
    metrics_api.get_inventory_status = wrapped_inventory
    metrics_api.get_attribution_metrics = wrapped_attribution
    metrics_api.get_total_metrics_summary = wrapped_total
    
    return metrics_api



