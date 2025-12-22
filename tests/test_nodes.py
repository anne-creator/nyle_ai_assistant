"""Tests for graph nodes."""
import pytest
from unittest.mock import patch, MagicMock


class TestClassifierNode:
    """Tests for the classifier node."""
    
    @patch("app.graph.nodes.classifier.node.ChatOpenAI")
    def test_classify_metrics_query(self, mock_llm, sample_state):
        """Test that metrics queries are classified correctly."""
        from app.graph.nodes.classifier.node import classify_question_node
        
        mock_response = MagicMock()
        mock_response.content = "metrics_query"
        mock_llm.return_value.invoke.return_value = mock_response
        
        sample_state["question"] = "What is my ACOS?"
        result = classify_question_node(sample_state)
        
        assert result["question_type"] == "metrics_query"
    
    @patch("app.graph.nodes.classifier.node.ChatOpenAI")
    def test_classify_comparison_query(self, mock_llm, comparison_state):
        """Test that comparison queries are classified correctly."""
        from app.graph.nodes.classifier.node import classify_question_node
        
        mock_response = MagicMock()
        mock_response.content = "compare_query"
        mock_llm.return_value.invoke.return_value = mock_response
        
        result = classify_question_node(comparison_state)
        
        assert result["question_type"] == "compare_query"
    
    @patch("app.graph.nodes.classifier.node.ChatOpenAI")
    def test_classify_asin_query(self, mock_llm, asin_state):
        """Test that ASIN queries are classified correctly."""
        from app.graph.nodes.classifier.node import classify_question_node
        
        mock_response = MagicMock()
        mock_response.content = "asin_product"
        mock_llm.return_value.invoke.return_value = mock_response
        
        result = classify_question_node(asin_state)
        
        assert result["question_type"] == "asin_product"
    
    @patch("app.graph.nodes.classifier.node.ChatOpenAI")
    def test_invalid_category_defaults_to_metrics(self, mock_llm, sample_state):
        """Test that invalid categories default to metrics_query."""
        from app.graph.nodes.classifier.node import classify_question_node
        
        mock_response = MagicMock()
        mock_response.content = "invalid_type"
        mock_llm.return_value.invoke.return_value = mock_response
        
        result = classify_question_node(sample_state)
        
        assert result["question_type"] == "metrics_query"


class TestDateExtractionNodes:
    """Tests for date extraction nodes."""
    
    def test_skip_extraction_when_dates_provided(self, sample_state):
        """Test that extraction is skipped when dates are already provided."""
        from app.graph.nodes.extract_dates_metrics.node import extract_dates_metrics_node
        
        sample_state["date_start"] = "2025-09-01"
        sample_state["date_end"] = "2025-09-14"
        
        result = extract_dates_metrics_node(sample_state)
        
        assert result["date_start"] == "2025-09-01"
        assert result["date_end"] == "2025-09-14"
    
    @patch("app.graph.nodes.extract_dates_metrics.node.ChatOpenAI")
    def test_extract_dates_metrics(self, mock_llm, sample_state):
        """Test date extraction for metrics queries."""
        from app.graph.nodes.extract_dates_metrics.node import extract_dates_metrics_node
        
        mock_structured = MagicMock()
        mock_structured.invoke.return_value = {
            "date_start": "2025-09-01",
            "date_end": "2025-09-14"
        }
        mock_llm.return_value.with_structured_output.return_value = mock_structured
        
        result = extract_dates_metrics_node(sample_state)
        
        assert result["date_start"] == "2025-09-01"
        assert result["date_end"] == "2025-09-14"


class TestHardcodedResponseNode:
    """Tests for hardcoded response node."""
    
    def test_performance_insights(self, sample_state):
        """Test performance insights response."""
        from app.graph.nodes.hardcoded_response.node import hardcoded_response_node
        
        sample_state["question"] = "Show me performance insights"
        result = hardcoded_response_node(sample_state)
        
        assert "Performance Insights" in result["response"]
    
    def test_highest_performance(self, sample_state):
        """Test highest performance response."""
        from app.graph.nodes.hardcoded_response.node import hardcoded_response_node
        
        sample_state["question"] = "What was the highest performance day?"
        result = hardcoded_response_node(sample_state)
        
        assert "highest performance day" in result["response"]
    
    def test_unknown_question(self, sample_state):
        """Test unknown question response."""
        from app.graph.nodes.hardcoded_response.node import hardcoded_response_node
        
        sample_state["question"] = "Something random"
        result = hardcoded_response_node(sample_state)
        
        assert "not sure how to answer" in result["response"]

