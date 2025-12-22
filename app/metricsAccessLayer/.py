"""
Nyle Backend API - Data Access Layer

This module provides a clean interface to all Nyle backend APIs.
Each method handles one endpoint and returns structured data.

Usage in handler tools:
    api = NyleBackendAPI()
    result = await api.get_ads_executive_summary(date_start, date_end)
"""

from typing import Optional
import logging

from app.api.client import BaseAPIClient

logger = logging.getLogger(__name__)


class NyleBackendAPI:
    """
    Data access layer for Nyle backend APIs.
    
    Automatically handles:
    - JWT authentication (from RequestContext)
    - Environment-based URL routing (dev vs prod)
    - HTTP error handling
    """
    
    def __init__(self):
        self.client = BaseAPIClient()
    
    async def get_ads_executive_summary(
        self,
        date_start: str,
        date_end: str,
        saturation: int = 0
    ) -> dict:
        """
        Fetch ads executive summary metrics.
        
        Args:
            date_start: Start date in YYYY-MM-DD format
            date_end: End date in YYYY-MM-DD format
            saturation: Saturation level (default: 0)
            
        Returns:
            Dict with ads summary metrics
            
        Example:
            api = NyleBackendAPI()
            result = await api.get_ads_executive_summary("2025-10-01", "2025-10-03")
        """
        endpoint = "/math/ads/executive-summary"
        params = {
            "date_start": date_start,
            "date_end": date_end,
            "saturation": saturation
        }
        
        logger.info(f"Fetching ads executive summary: {date_start} to {date_end}")
        return await self.client.get(endpoint, params)
    
    async def get_financial_summary(
        self,
        date_start: str,
        date_end: str
    ) -> dict:
        """
        Fetch financial summary metrics.
        
        Args:
            date_start: Start date in YYYY-MM-DD format
            date_end: End date in YYYY-MM-DD format
            
        Returns:
            Dict with financial metrics
        """
        endpoint = "/math/financial/summary"
        params = {
            "date_start": date_start,
            "date_end": date_end
        }
        
        logger.info(f"Fetching financial summary: {date_start} to {date_end}")
        return await self.client.get(endpoint, params)
    
    async def get_organic_metrics(
        self,
        date_start: str,
        date_end: str
    ) -> dict:
        """
        Fetch organic performance metrics.
        
        Args:
            date_start: Start date in YYYY-MM-DD format
            date_end: End date in YYYY-MM-DD format
            
        Returns:
            Dict with organic metrics
        """
        endpoint = "/math/organic/metrics"
        params = {
            "date_start": date_start,
            "date_end": date_end
        }
        
        logger.info(f"Fetching organic metrics: {date_start} to {date_end}")
        return await self.client.get(endpoint, params)
    
    async def get_inventory_status(
        self,
        date_start: str,
        date_end: str,
        asin: Optional[str] = None
    ) -> dict:
        """
        Fetch inventory status and predictions.
        
        Args:
            date_start: Start date in YYYY-MM-DD format
            date_end: End date in YYYY-MM-DD format
            asin: Optional ASIN to filter by specific product
            
        Returns:
            Dict with inventory data
        """
        endpoint = "/math/inventory/status"
        params = {
            "date_start": date_start,
            "date_end": date_end
        }
        if asin:
            params["asin"] = asin
        
        logger.info(f"Fetching inventory status: {date_start} to {date_end}")
        return await self.client.get(endpoint, params)
    
    async def get_attribution_metrics(
        self,
        date_start: str,
        date_end: str
    ) -> dict:
        """
        Fetch attribution metrics.
        
        Args:
            date_start: Start date in YYYY-MM-DD format
            date_end: End date in YYYY-MM-DD format
            
        Returns:
            Dict with attribution metrics
        """
        endpoint = "/math/attribution/metrics"
        params = {
            "date_start": date_start,
            "date_end": date_end
        }
        
        logger.info(f"Fetching attribution metrics: {date_start} to {date_end}")
        return await self.client.get(endpoint, params)
    
    async def get_product_performance(
        self,
        date_start: str,
        date_end: str,
        asin: str
    ) -> dict:
        """
        Fetch performance metrics for a specific product (ASIN).
        
        Args:
            date_start: Start date in YYYY-MM-DD format
            date_end: End date in YYYY-MM-DD format
            asin: Product ASIN identifier
            
        Returns:
            Dict with product-specific metrics
        """
        endpoint = f"/math/products/{asin}/performance"
        params = {
            "date_start": date_start,
            "date_end": date_end
        }
        
        logger.info(f"Fetching product performance for {asin}: {date_start} to {date_end}")
        return await self.client.get(endpoint, params)

