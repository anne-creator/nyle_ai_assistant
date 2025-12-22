"""Tests for API access layer."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestBaseAPIClient:
    """Tests for BaseAPIClient."""
    
    @patch("app.api.client.get_settings")
    def test_get_base_url_dev(self, mock_settings):
        """Test base URL selection for dev environment."""
        from app.api.client import BaseAPIClient
        
        mock_settings.return_value.environment = "dev"
        mock_settings.return_value.dev_api_base_url = "https://api0.dev.nyle.ai/math/v1"
        mock_settings.return_value.prod_api_base_url = "https://api.nyle.ai/math/v1"
        
        client = BaseAPIClient()
        
        assert client.base_url == "https://api0.dev.nyle.ai/math/v1"
    
    @patch("app.api.client.get_settings")
    def test_get_base_url_local(self, mock_settings):
        """Test base URL selection for local environment (uses prod)."""
        from app.api.client import BaseAPIClient
        
        mock_settings.return_value.environment = "local"
        mock_settings.return_value.dev_api_base_url = "https://api0.dev.nyle.ai/math/v1"
        mock_settings.return_value.prod_api_base_url = "https://api.nyle.ai/math/v1"
        
        client = BaseAPIClient()
        
        assert client.base_url == "https://api.nyle.ai/math/v1"
    
    @patch("app.api.client.get_settings")
    def test_get_base_url_production(self, mock_settings):
        """Test base URL selection for production environment."""
        from app.api.client import BaseAPIClient
        
        mock_settings.return_value.environment = "production"
        mock_settings.return_value.dev_api_base_url = "https://api0.dev.nyle.ai/math/v1"
        mock_settings.return_value.prod_api_base_url = "https://api.nyle.ai/math/v1"
        
        client = BaseAPIClient()
        
        assert client.base_url == "https://api.nyle.ai/math/v1"


class TestNyleAPI:
    """Tests for NyleAPI."""
    
    @pytest.mark.asyncio
    @patch("app.api.nyle_api.BaseAPIClient")
    async def test_get_ads_executive_summary(self, mock_client_class):
        """Test NyleAPI.get_ads_executive_summary() calls the right endpoint."""
        from app.api.nyle_api import NyleAPI
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value={"acos": 0.25, "ad_spend": 1000})
        mock_client_class.return_value = mock_client
        
        api = NyleAPI()
        result = await api.get_ads_executive_summary("2025-10-01", "2025-10-03")
        
        assert "acos" in result
        assert result["acos"] == 0.25
        mock_client.get.assert_called_once()
        
        # Verify correct endpoint
        call_args = mock_client.get.call_args
        assert "/math/ads/executive-summary" in call_args[0][0]
    
    @pytest.mark.asyncio
    @patch("app.api.nyle_api.BaseAPIClient")
    async def test_get_financial_summary(self, mock_client_class):
        """Test financial summary endpoint."""
        from app.api.nyle_api import NyleAPI
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value={"net_profit": 50000})
        mock_client_class.return_value = mock_client
        
        api = NyleAPI()
        result = await api.get_financial_summary("2025-10-01", "2025-10-03")
        
        assert "net_profit" in result
        mock_client.get.assert_called_once()
