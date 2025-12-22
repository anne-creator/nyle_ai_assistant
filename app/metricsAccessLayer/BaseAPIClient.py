import httpx
from typing import Optional
import logging

from app.config import get_settings
from app.context import get_jwt_token

logger = logging.getLogger(__name__)


class BaseAPIClient:
    """Base HTTP client with environment-aware URL selection."""
    
    def __init__(self):
        settings = get_settings()
        self.base_url = self._get_base_url(settings)
        self.timeout = 30.0
    
    def _get_base_url(self, settings) -> str:
        """Get base URL based on environment. Local and prod use prod URL."""
        if settings.environment == "dev":
            return settings.dev_api_base_url
        return settings.prod_api_base_url
    
    def _get_headers(self) -> dict:
        """Get headers with JWT from context."""
        jwt_token = get_jwt_token()
        return {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }
    
    async def get(self, endpoint: str, params: Optional[dict] = None) -> dict:
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
    
    async def post(self, endpoint: str, data: Optional[dict] = None) -> dict:
        """Make POST request."""
        url = f"{self.base_url}{endpoint}"
        logger.info(f"POST {url}")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=data
            )
            response.raise_for_status()
            return response.json()

