"""
Math Metric Retriever - Data Access Layer with Singleton Pattern

All 6 Nyle backend API endpoints in one place.
Singleton pattern ensures only one instance is created.

Usage anywhere in your project:
    from app.metricsAccessLayer.math_metric_retriver import metrics_api
    
    result = await metrics_api.get_financial_summary("2025-10-01", "2025-10-31")
"""

from typing import Optional
import logging

from app.metricsAccessLayer.BaseAPIClient import BaseAPIClient

logger = logging.getLogger(__name__)


class MathMetricRetriever:
    """
    Singleton data access layer for Nyle math backend APIs.
    
    Automatically handles:
    - JWT authentication (from RequestContext)
    - Environment-based URL routing (dev vs prod)
    - HTTP error handling
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern - only create one instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize only once."""
        if self._initialized:
            return
        self.client = BaseAPIClient()
        self._initialized = True
    
    # ========== API 1: Ads Executive Summary ==========
    async def get_ads_executive_summary(
        self,
        date_start: str,
        date_end: str,
        saturation: int = 0
    ) -> dict:
        """
        GET /math/ads/executive-summary
        
        Returns advertising metrics summary.
        """
        endpoint = "/math/ads/executive-summary"
        params = {
            "date_start": date_start,
            "date_end": date_end,
            "saturation": saturation
        }
        
        logger.info(f"Calling {endpoint}")
        return await self.client.get(endpoint, params)
    
    # ========== API 2: Financial Summary ==========
    async def get_financial_summary(
        self,
        date_start: str,
        date_end: str
    ) -> dict:
        """
        GET /math/cfo/executive-summary
        
        Returns CFO/financial metrics.
        """
        endpoint = "/math/cfo/executive-summary"
        params = {
            "date_start": date_start,
            "date_end": date_end
        }
        
        logger.info(f"Calling {endpoint}")
        return await self.client.get(endpoint, params)
    
    # ========== API 3: Organic Metrics ==========
    async def get_organic_metrics(
        self,
        date_start: str,
        date_end: str
    ) -> dict:
        """
        GET /math/organic/executive-summary
        
        Returns organic performance metrics.
        """
        endpoint = "/math/organic/executive-summary"
        params = {
            "date_start": date_start,
            "date_end": date_end
        }
        
        logger.info(f"Calling {endpoint}")
        return await self.client.get(endpoint, params)
    
    # ========== API 4: Inventory Status ==========
    async def get_inventory_status(
        self,
        date_start: str,
        date_end: str,
        asin: Optional[str] = None
    ) -> dict:
        """
        GET /math/inventory/metrics/executive-summary
        
        Returns inventory data, optionally filtered by ASIN.
        """
        endpoint = "/math/inventory/metrics/executive-summary"
        params = {
            "date_start": date_start,
            "date_end": date_end
        }
        if asin:
            params["asin"] = asin
        
        logger.info(f"Calling {endpoint}")
        return await self.client.get(endpoint, params)
    
    # ========== API 5: Attribution Metrics ==========
    async def get_attribution_metrics(
        self,
        date_start: str,
        date_end: str
    ) -> dict:
        """
        GET /math/attribution/metrics
        
        Returns attribution metrics.
        """
        endpoint = "/math/attribution/executive-summary"
        params = {
            "date_start": date_start,
            "date_end": date_end
        }
        
        logger.info(f"Calling {endpoint}")
        return await self.client.get(endpoint, params)
    
    # ========== API 6: Total Metrics Executive Summary ==========
    async def get_total_metrics_summary(
        self,
        date_start: str,
        date_end: str
    ) -> dict:
        """
        GET /math/total/executive-summary

        Returns total summary metrics across all areas.
        """
        endpoint = "/math/total/executive-summary"
        params = {
            "date_start": date_start,
            "date_end": date_end
        }

        logger.info(f"Calling {endpoint}")
        return await self.client.get(endpoint, params)


# ========== Singleton Instance - Use this everywhere ==========
metrics_api = MathMetricRetriever()
