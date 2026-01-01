"""
Products API Client - Data Access Layer for /amazon/v1/products/* endpoints.

Singleton pattern ensures only one instance is created.

Usage anywhere in your project:
    from app.metricsAccessLayer.products_api import products_api
    
    result = await products_api.get_ranked_products(limit=5, order_direction=1)
"""

from typing import List, Optional
import logging
import httpx

from app.config import get_settings
from app.context import get_jwt_token

logger = logging.getLogger(__name__)


class ProductsAPIClient:
    """
    Singleton data access layer for Nyle products APIs.
    
    Uses a different base URL than MathMetricRetriever because
    products endpoints are at /amazon/v1/* not /math/v1/*.
    
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
        settings = get_settings()
        # Use root API URL (without /math/v1 suffix) for products endpoints
        if settings.environment == "dev":
            self.base_url = "https://api0.dev.nyle.ai"
        else:
            self.base_url = "https://api.nyle.ai"
        self.timeout = 30.0
        self._initialized = True
    
    def _get_headers(self) -> dict:
        """Get headers with JWT from context."""
        jwt_token = get_jwt_token()
        return {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }
    
    async def _get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Make GET request."""
        url = f"{self.base_url}{endpoint}"
        logger.info(f"GET {url}")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                url,
                headers=self._get_headers(),
                params=params
            )
            response.raise_for_status()
            return response.json()
    
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
        return await self._get(endpoint, params)
    
    # ========== API: Get Product Details by ASIN ==========
    async def get_product_details(self, asin: str) -> dict:
        """
        GET /amazon/v1/products/own/{asin}
        
        Returns product details including image_link.
        
        Args:
            asin: Product ASIN code (e.g., "B07YN9JXNW")
            
        Returns:
            Product dict with:
            - asin, item_name, item_description
            - image_link: Amazon CDN URL
            - price, brand, bullet_points
            - executive_summary: metrics dict
            - link: Amazon product page URL
        """
        endpoint = f"/amazon/v1/products/own/{asin}"
        logger.info(f"Fetching product details for ASIN: {asin}")
        return await self._get(endpoint)


# ========== Singleton Instance - Use this everywhere ==========
products_api = ProductsAPIClient()

