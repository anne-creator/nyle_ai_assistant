"""
Metrics Access Layer

Data access layer for Nyle backend APIs.

Usage:
    from app.metricsAccessLayer import metrics_api, products_api
    
    result = await metrics_api.get_financial_summary("2025-10-01", "2025-10-31")
    products = await products_api.get_ranked_products(limit=5, order_direction=1)
"""

from app.metricsAccessLayer.math_metric_retriver import MathMetricRetriever, metrics_api
from app.metricsAccessLayer.products_api import ProductsAPIClient, products_api
from app.metricsAccessLayer.BaseAPIClient import BaseAPIClient

__all__ = ["MathMetricRetriever", "ProductsAPIClient", "BaseAPIClient", "metrics_api", "products_api"]
