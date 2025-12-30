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
        asin: Optional[str] = None,
        saturation: int = 0,
        timespan: Optional[str] = None
    ) -> dict:
        """
        GET /math/ads/executive-summary
        
        Returns advertising metrics summary, optionally filtered by ASIN.
        """
        endpoint = "/math/ads/executive-summary"
        params = {
            "date_start": date_start,
            "date_end": date_end,
            "saturation": saturation
        }
        if asin:
            params["asin"] = asin
        if timespan:
            params["timespan"] = timespan
        
        logger.info(f"Calling {endpoint}")
        return await self.client.get(endpoint, params)
    
    # ========== API 2: Financial Summary ==========
    async def get_financial_summary(
        self,
        date_start: str,
        date_end: str,
        asin: Optional[str] = None,
        timespan: Optional[str] = None
    ) -> dict:
        """
        GET /math/cfo/executive-summary
        
        Returns CFO/financial metrics, optionally filtered by ASIN.
        """
        endpoint = "/math/cfo/executive-summary"
        params = {
            "date_start": date_start,
            "date_end": date_end
        }
        if asin:
            params["asin"] = asin
        if timespan:
            params["timespan"] = timespan
        
        logger.info(f"Calling {endpoint}")
        return await self.client.get(endpoint, params)
    
    # ========== API 3: Organic Metrics ==========
    async def get_organic_metrics(
        self,
        date_start: str,
        date_end: str,
        timespan: Optional[str] = None
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
        if timespan:
            params["timespan"] = timespan
        
        logger.info(f"Calling {endpoint}")
        return await self.client.get(endpoint, params)
    
    # ========== API 4: Inventory Status ==========
    async def get_inventory_status(
        self,
        date_start: str,
        date_end: str,
        asin: Optional[str] = None,
        timespan: Optional[str] = None
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
        if timespan:
            params["timespan"] = timespan
        
        logger.info(f"Calling {endpoint}")
        return await self.client.get(endpoint, params)
    
    # ========== API 5: Attribution Metrics ==========
    async def get_attribution_metrics(
        self,
        date_start: str,
        date_end: str,
        timespan: Optional[str] = None
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
        if timespan:
            params["timespan"] = timespan
        
        logger.info(f"Calling {endpoint}")
        return await self.client.get(endpoint, params)
    
    # ========== API 6: Total Metrics Executive Summary ==========
    async def get_total_metrics_summary(
        self,
        date_start: str,
        date_end: str,
        asin: Optional[str] = None,
        timespan: Optional[str] = None
    ) -> dict:
        """
        GET /math/total/executive-summary

        Returns total summary metrics across all areas, optionally filtered by ASIN.
        """
        endpoint = "/math/total/executive-summary"
        params = {
            "date_start": date_start,
            "date_end": date_end
        }
        if asin:
            params["asin"] = asin
        if timespan:
            params["timespan"] = timespan

        logger.info(f"Calling {endpoint}")
        return await self.client.get(endpoint, params)

    # ========== API 7: Combined Ads & Organic Keywords ==========
    async def get_combined_ads_organic_keywords(
        self,
        date_start: str,
        date_end: str,
        sort_field: Optional[str] = None,
        sort_direction: Optional[str] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        country: Optional[str] = None,
        asin: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> dict:
        """
        GET /math/combined/ads_organic_keywords

        Returns paginated list of search terms with combined ads + organic metrics.

        Args:
            date_start: Start date of the query range (YYYY-MM-DD) - Required
            date_end: End date of the query range (YYYY-MM-DD) - Required
            sort_field: Field to sort results by (e.g., 'combined_sales')
            sort_direction: Sort order ('asc' or 'desc')
            offset: Number of items to skip for pagination
            limit: Max number of items to return per page
            country: Country/marketplace code to filter by (e.g., US, UK, DE)
            asin: Amazon Standard Identification Number to filter by
            search_query: Partial match filter for search terms (case-insensitive)
        """
        endpoint = "/math/combined/ads_organic_keywords"
        params = {
            "date_start": date_start,
            "date_end": date_end
        }
        if sort_field:
            params["sort_field"] = sort_field
        if sort_direction:
            params["sort_direction"] = sort_direction
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit
        if country:
            params["country"] = country
        if asin:
            params["asin"] = asin
        if search_query:
            params["search_query"] = search_query

        logger.info(f"Calling {endpoint}")
        return await self.client.get(endpoint, params)


# ========== Singleton Instance - Use this everywhere ==========
metrics_api = MathMetricRetriever()
