"""
Metrics Access Layer

Data access layer for Nyle math backend APIs.

Usage:
    from app.metricsAccessLayer import metrics_api
    
    result = await metrics_api.get_financial_summary("2025-10-01", "2025-10-31")
"""

from app.metricsAccessLayer.math_metric_retriver import MathMetricRetriever, metrics_api
from app.metricsAccessLayer.BaseAPIClient import BaseAPIClient

__all__ = ["MathMetricRetriever", "BaseAPIClient", "metrics_api"]
