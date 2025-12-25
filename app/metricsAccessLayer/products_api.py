"""
Products API Client - Data Access Layer for /amazon/v1/products/* endpoints.

Singleton pattern ensures only one instance is created.

Usage anywhere in your project:
    from app.metricsAccessLayer.products_api import products_api
    
    result = await products_api.get_ranked_products(limit=5, order_direction=1)
"""

from typing import List, Optional
import logging

from app.metricsAccessLayer.BaseAPIClient import BaseAPIClient

logger = logging.getLogger(__name__)


class ProductsAPIClient:
    """
    Singleton data access layer for Nyle products APIs.
    
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
    
    # ========== API: Get Ranked Products ==========
    async def get_ranked_products(
        self,
        offset: int = 0,
        limit: int = 10,
        order_direction: int = 1,
        order_by: str = "executive_summary.total_sales"
    ) -> List[dict]:
        """
        GET /amazon/v1/products/own
        
        Returns ranked list of products with executive_summary metrics.
        
        Args:
            offset: Pagination start (default: 0)
            limit: Number of products to return
            order_direction: 1=descending (top/best), 0=ascending (lowest/worst)
            order_by: Field to sort by (e.g., 'executive_summary.total_sales')
            
        Returns:
            List of product dicts with asin, item_name, price, brand, executive_summary
        """
        endpoint = "/amazon/v1/products/own"
        params = {
            "offset": offset,
            "limit": limit,
            "order_direction": order_direction,
            "order_by": order_by
        }
        
        logger.info(f"Calling {endpoint} with params: {params}")
        return await self.client.get(endpoint, params)


# ========== Singleton Instance - Use this everywhere ==========
products_api = ProductsAPIClient()

