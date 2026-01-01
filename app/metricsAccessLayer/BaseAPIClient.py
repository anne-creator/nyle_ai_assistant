import httpx
from typing import Optional
import logging

from app.config import get_settings
from app.context import get_jwt_token

logger = logging.getLogger(__name__)


class BaseAPIClient:
    """
    Base HTTP client with environment-aware URL selection.
    
    Supports both Math backend (/math/v1/*) and Amazon backend (/amazon/v1/*) APIs.
    """
    
    def __init__(self, api_prefix: str = "/math/v1"):
        """
        Initialize API client with specific API prefix.
        
        Args:
            api_prefix: API path prefix (e.g., "/math/v1" or "/amazon/v1")
        """
        settings = get_settings()
        self.base_url = self._get_base_url(settings, api_prefix)
        self.timeout = 30.0
    
    def _get_base_url(self, settings, api_prefix: str) -> str:
        """
        Get base URL based on environment. Local and prod use prod URL.
        
        Args:
            api_prefix: API path prefix to append to base URL
        """
        if settings.environment == "dev":
            base = "https://api0.dev.nyle.ai"
        else:
            base = "https://api.nyle.ai"
        
        return f"{base}{api_prefix}"
    
    def _get_headers(self) -> dict:
        """Get headers with JWT from context."""
        jwt_token = get_jwt_token()
        logger.debug(f"JWT token retrieved: {jwt_token[:20] if jwt_token else 'None'}...")
        if not jwt_token:
            logger.error("No JWT token available in context!")
            raise RuntimeError("No JWT token available in request context")
        return {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }
    
    async def get(self, endpoint: str, params: Optional[dict] = None, timeout: Optional[float] = None) -> dict:
        """Make GET request."""
        url = f"{self.base_url}{endpoint}"
        request_timeout = timeout or self.timeout
        logger.info(f"GET {url} with params: {params}, timeout: {request_timeout}s")
        
        try:
            async with httpx.AsyncClient(timeout=request_timeout) as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    params=params
                )
                response.raise_for_status()
                return response.json()
        except httpx.ReadTimeout:
            logger.error(f"Timeout after {request_timeout}s calling {endpoint} with params {params}")
            raise
    
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

