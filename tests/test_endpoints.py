"""Tests for FastAPI endpoints."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient


class TestChatbotEndpoint:
    """Tests for /chatbot endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from app.main import app
        return TestClient(app)
    
    def test_requires_authorization(self, client):
        """Test that endpoint requires JWT."""
        response = client.post(
            "/chatbot",
            json={
                "message": "What is my ACOS?",
                "sessionId": "test"
            }
        )
        assert response.status_code == 401
    
    def test_invalid_authorization_format(self, client):
        """Test that invalid auth format is rejected."""
        response = client.post(
            "/chatbot",
            headers={"Authorization": "InvalidFormat"},
            json={
                "message": "What is my ACOS?",
                "sessionId": "test"
            }
        )
        assert response.status_code == 401
    
    @patch("app.main.graph")
    def test_successful_request(self, mock_graph, client):
        """Test successful chatbot request."""
        mock_graph.ainvoke = AsyncMock(return_value={
            "response": "Your ACOS is **25.5%** (Sep 1-14, 2025)"
        })
        
        response = client.post(
            "/chatbot",
            headers={"Authorization": "Bearer test-jwt"},
            json={
                "message": "What is my ACOS?",
                "sessionId": "test"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "myField" in data
    
    @patch("app.main.graph")
    def test_with_date_params(self, mock_graph, client):
        """Test request with date parameters."""
        mock_graph.ainvoke = AsyncMock(return_value={
            "response": "Your ACOS is **25.5%**"
        })
        
        response = client.post(
            "/chatbot",
            headers={"Authorization": "Bearer test-jwt"},
            json={
                "message": "What is my ACOS?",
                "sessionId": "test",
                "date_start": "2025-09-01",
                "date_end": "2025-09-14"
            }
        )
        
        assert response.status_code == 200


class TestHealthEndpoint:
    """Tests for /health endpoint."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from app.main import app
        return TestClient(app)
    
    def test_health_check(self, client):
        """Test health check returns ok."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

