Updated Migration Guide: 5-Node Graph with Conditional Routing
New Graph Structure
                            START
                              ↓
                    ┌──────────────────┐
                    │  1. CLASSIFIER   │ ← Determines question type
                    └──────────────────┘
                              ↓
            ┌─────────────────┼─────────────────┬──────────────────┐
            ↓                 ↓                 ↓                  ↓
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐
    │ Extract Dates│  │ Extract Dates│  │ Extract Dates│  │  Hardcoded  │
    │  (Metrics)   │  │ (Comparison) │  │   (ASIN)     │  │  Response   │
    └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘
            ↓                 ↓                 ↓                  ↓
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
    │ 2. Metrics   │  │ 3. Comparison│  │ 4. ASIN      │         │
    │    Query     │  │    Query     │  │   Product    │         │
    │   Handler    │  │   Handler    │  │   Handler    │         │
    └──────────────┘  └──────────────┘  └──────────────┘         │
            ↓                 ↓                 ↓                  ↓
            └─────────────────┴─────────────────┴──────────────────┘
                                      ↓
                                    END
4 Question Types:

metrics_query - Regular metric questions
compare_query - Comparison questions (2 periods)
asin_product - ASIN-specific questions
hardcoded - Hardcoded responses (performance_compare, highest_performance)


Updated State Schema
python# app/models/state.py
from typing import TypedDict, List, Optional, Literal
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """State passed through the LangGraph execution"""
    
    # Core conversation
    messages: List[BaseMessage]
    question: str
    
    # PRIMARY date parameters (always present after extraction)
    date_start: str
    date_end: str
    
    # COMPARISON date parameters (for compare_query type)
    compare_date_start: Optional[str]
    compare_date_end: Optional[str]
    
    # ASIN parameter (for asin_product type)
    asin: Optional[str]
    
    # Question routing
    question_type: Literal[
        "metrics_query",      # Single period metric questions
        "compare_query",      # Two period comparisons
        "asin_product",       # ASIN-specific questions
        "hardcoded"           # Hardcoded responses
    ]
    
    # Metrics processing
    requested_metrics: Optional[List[str]]
    metric_data: Optional[dict]
    comparison_metric_data: Optional[dict]
    
    # Final output
    response: str

Updated Graph Builder
python# app/graph/builder.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.models.state import AgentState
from app.graph.nodes import (
    classify_question_node,
    extract_dates_metrics_node,
    extract_dates_comparison_node,
    extract_dates_asin_node,
    metrics_query_handler_node,
    compare_query_handler_node,
    asin_product_handler_node,
    hardcoded_response_node
)

def create_chatbot_graph():
    """
    Build the chatbot graph with conditional routing.
    
    Flow:
    1. Classify question type
    2. Route to appropriate handler based on type
    3. Each handler extracts its own dates first, then processes
    """
    
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add classifier node
    workflow.add_node("classify", classify_question_node)
    
    # Add date extraction nodes (one per type)
    workflow.add_node("extract_dates_metrics", extract_dates_metrics_node)
    workflow.add_node("extract_dates_comparison", extract_dates_comparison_node)
    workflow.add_node("extract_dates_asin", extract_dates_asin_node)
    
    # Add handler nodes
    workflow.add_node("metrics_query_handler", metrics_query_handler_node)
    workflow.add_node("compare_query_handler", compare_query_handler_node)
    workflow.add_node("asin_product_handler", asin_product_handler_node)
    workflow.add_node("hardcoded_response", hardcoded_response_node)
    
    # Set entry point
    workflow.set_entry_point("classify")
    
    # Conditional routing after classification
    def route_by_question_type(state: AgentState) -> str:
        """Route to appropriate date extraction based on question type"""
        question_type = state.get("question_type", "metrics_query")
        
        routing_map = {
            "metrics_query": "extract_dates_metrics",
            "compare_query": "extract_dates_comparison",
            "asin_product": "extract_dates_asin",
            "hardcoded": "hardcoded_response"
        }
        
        return routing_map.get(question_type, "extract_dates_metrics")
    
    workflow.add_conditional_edges(
        "classify",
        route_by_question_type,
        {
            "extract_dates_metrics": "extract_dates_metrics",
            "extract_dates_comparison": "extract_dates_comparison",
            "extract_dates_asin": "extract_dates_asin",
            "hardcoded_response": "hardcoded_response"
        }
    )
    
    # Connect date extraction to handlers
    workflow.add_edge("extract_dates_metrics", "metrics_query_handler")
    workflow.add_edge("extract_dates_comparison", "compare_query_handler")
    workflow.add_edge("extract_dates_asin", "asin_product_handler")
    
    # All handlers end the flow
    workflow.add_edge("metrics_query_handler", END)
    workflow.add_edge("compare_query_handler", END)
    workflow.add_edge("asin_product_handler", END)
    workflow.add_edge("hardcoded_response", END)
    
    # Add memory for conversation history
    memory = MemorySaver()
    
    return workflow.compile(checkpointer=memory)

Node Implementations
Node 1: Classifier (Updated)
python# app/graph/nodes.py
from langchain_openai import ChatOpenAI
from app.models.state import AgentState
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

def classify_question_node(state: AgentState) -> AgentState:
    """
    Node 1: Classify question into one of 4 types.
    
    Types:
    - metrics_query: Regular metric questions (ACOS, sales, profit, etc.)
    - compare_query: Comparison questions (August vs September, Q1 vs Q2)
    - asin_product: ASIN-specific questions (about a specific product)
    - hardcoded: Questions with hardcoded responses
    """
    
    logger.info(f"🏷️  Classifying: '{state['question']}'")
    
    settings = get_settings()
    llm = ChatOpenAI(model=settings.openai_model, temperature=0)
    
    prompt = f"""Classify this Amazon seller question into ONE category:

**Categories:**

1. **metrics_query** - Questions about store-level metrics
   Examples:
   - "What is my ACOS?"
   - "Show me total sales for last month"
   - "What was my net profit yesterday?"
   - "Give me my store overview"

2. **compare_query** - Questions comparing TWO time periods
   Examples:
   - "Compare August vs September"
   - "How did sales change from last month to this month?"
   - "Show Q1 compared to Q2"
   - "What's the difference between last week and this week?"

3. **asin_product** - Questions about a SPECIFIC product (ASIN)
   Examples:
   - "What are sales for ASIN B0B5HN65QQ?"
   - "Show me performance of product B0DP55J8ZG"
   - "How is ASIN B0D3VHMR3Z doing?"
   - "When will B0B5HN65QQ go out of stock?"

4. **hardcoded** - Special questions with pre-defined responses
   Examples:
   - "Show me performance insights"
   - "What was the highest performance day?"

**Question:** {state['question']}

**Return ONLY the category name (no explanation).**"""

    response = llm.invoke(prompt)
    question_type = response.content.strip()
    
    # Validate category
    valid_types = ["metrics_query", "compare_query", "asin_product", "hardcoded"]
    if question_type not in valid_types:
        logger.warning(f"Invalid category '{question_type}', defaulting to metrics_query")
        question_type = "metrics_query"
    
    state["question_type"] = question_type
    logger.info(f"✓ Question type: {question_type}")
    
    return state

Date Extraction Nodes (3 Variants)
Extract Dates - Metrics Query
pythondef extract_dates_metrics_node(state: AgentState) -> AgentState:
    """
    Extract date range for metrics_query type questions.
    
    This handles single-period questions like:
    - "What is my ACOS?"
    - "Show me last month's sales"
    """
    
    logger.info(f"📅 Extracting dates for metrics_query")
    
    # If dates already provided by frontend, skip
    if state.get("date_start") and state.get("date_end"):
        logger.info("✓ Dates already provided, skipping extraction")
        return state
    
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0
    ).with_structured_output(
        schema={
            "type": "object",
            "properties": {
                "date_start": {"type": "string"},
                "date_end": {"type": "string"}
            },
            "required": ["date_start", "date_end"]
        }
    )
    
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""Extract date range for metrics query. Today is {current_date}.

Rules:
- "yesterday" → {current_date} minus 1 day
- "last week" → 7 days ago to yesterday
- "past month" → 30 days ago to today
- "this month" → first day of month to today
- "August" → 2025-08-01 to 2025-08-31
- No time reference → 7 days ago to today (default)

Question: {state['question']}

Return JSON with date_start and date_end (YYYY-MM-DD)."""

    dates = llm.invoke(prompt)
    
    state["date_start"] = dates["date_start"]
    state["date_end"] = dates["date_end"]
    
    logger.info(f"✓ Extracted: {state['date_start']} to {state['date_end']}")
    
    return state
Extract Dates - Comparison Query
pythondef extract_dates_comparison_node(state: AgentState) -> AgentState:
    """
    Extract TWO date ranges for compare_query type questions.
    
    This handles comparison questions like:
    - "Compare August vs September"
    - "How did sales change from Q1 to Q2?"
    """
    
    logger.info(f"📅 Extracting dates for compare_query")
    
    # If dates already provided by frontend, skip
    if (state.get("date_start") and state.get("date_end") and 
        state.get("compare_date_start") and state.get("compare_date_end")):
        logger.info("✓ Dates already provided, skipping extraction")
        return state
    
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0
    ).with_structured_output(
        schema={
            "type": "object",
            "properties": {
                "date_start": {"type": "string"},
                "date_end": {"type": "string"},
                "compare_date_start": {"type": "string"},
                "compare_date_end": {"type": "string"}
            },
            "required": ["date_start", "date_end", "compare_date_start", "compare_date_end"]
        }
    )
    
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""Extract TWO date ranges for comparison. Today is {current_date}.

The question asks to compare two periods. Extract:
- date_start/date_end = MORE RECENT period
- compare_date_start/compare_date_end = EARLIER period

Examples:
- "Compare August vs September" →
  date_start: 2025-09-01, date_end: 2025-09-30 (September)
  compare_date_start: 2025-08-01, compare_date_end: 2025-08-31 (August)

- "How did sales change from last month to this month?" →
  date_start: 2025-12-01, date_end: 2025-12-20 (this month)
  compare_date_start: 2025-11-01, compare_date_end: 2025-11-30 (last month)

Question: {state['question']}

Return JSON with all 4 date fields (YYYY-MM-DD)."""

    dates = llm.invoke(prompt)
    
    state["date_start"] = dates["date_start"]
    state["date_end"] = dates["date_end"]
    state["compare_date_start"] = dates["compare_date_start"]
    state["compare_date_end"] = dates["compare_date_end"]
    
    logger.info(f"✓ Current period: {state['date_start']} to {state['date_end']}")
    logger.info(f"✓ Compare period: {state['compare_date_start']} to {state['compare_date_end']}")
    
    return state
Extract Dates - ASIN Product Query
pythondef extract_dates_asin_node(state: AgentState) -> AgentState:
    """
    Extract date range AND ASIN for asin_product type questions.
    
    This handles ASIN-specific questions like:
    - "What are sales for ASIN B0B5HN65QQ?"
    - "When will product B0DP55J8ZG go out of stock?"
    """
    
    logger.info(f"📅 Extracting dates and ASIN for asin_product query")
    
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0
    ).with_structured_output(
        schema={
            "type": "object",
            "properties": {
                "asin": {"type": "string"},
                "date_start": {"type": "string"},
                "date_end": {"type": "string"}
            },
            "required": ["asin", "date_start", "date_end"]
        }
    )
    
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""Extract ASIN and date range. Today is {current_date}.

Extract:
1. ASIN - The product identifier (format: B0XXXXXXXXX)
2. Date range - Same rules as metrics queries

Date rules:
- "yesterday" → {current_date} minus 1 day
- "last week" → 7 days ago to yesterday
- "past month" → 30 days ago to today
- No time reference → 7 days ago to today (default)

Question: {state['question']}

Return JSON with asin, date_start, and date_end."""

    result = llm.invoke(prompt)
    
    state["asin"] = result["asin"]
    state["date_start"] = result["date_start"]
    state["date_end"] = result["date_end"]
    
    logger.info(f"✓ ASIN: {state['asin']}")
    logger.info(f"✓ Date range: {state['date_start']} to {state['date_end']}")
    
    return state

Handler Nodes
Metrics Query Handler
pythonfrom langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from typing import List
from app.services.metrics_api import MetricsAccessLayer

def metrics_query_handler_node(state: AgentState) -> AgentState:
    """
    Handler for metrics_query type questions.
    
    Handles questions like:
    - "What is my ACOS?"
    - "Show me total sales"
    - "Give me store overview"
    """
    
    logger.info(f"💬 Processing metrics_query: '{state['question']}'")
    
    settings = get_settings()
    
    # Define tool for fetching metrics
    @tool
    async def get_metrics(metrics: List[str]) -> dict:
        """Fetch live metrics from Amazon Seller APIs.
        
        Args:
            metrics: List of metric names (e.g., ["acos", "total_sales", "net_profit"])
            
        Returns:
            Dictionary with metric names as keys and numeric values
        """
        logger.info(f"🔧 Tool: get_metrics({metrics})")
        
        access_layer = MetricsAccessLayer()
        result = await access_layer.get_metrics(
            metrics,
            state["date_start"],
            state["date_end"]
        )
        
        logger.info(f"✓ Retrieved {len(result)} metrics")
        return result
    
    # Create AI agent
    llm = ChatOpenAI(model=settings.openai_model, temperature=0)
    
    agent = create_react_agent(
        llm,
        tools=[get_metrics],
        state_modifier=METRICS_QUERY_SYSTEM_PROMPT
    )
    
    # Run agent
    logger.info("🤖 Running metrics query agent...")
    
    result = agent.invoke({
        "messages": [(
            "human",
            f"Question: {state['question']}\nDate: {state['date_start']} to {state['date_end']}"
        )]
    })
    
    state["response"] = result["messages"][-1].content
    logger.info(f"✓ Generated response")
    
    return state

# System prompt for metrics query handler
METRICS_QUERY_SYSTEM_PROMPT = """You are an Amazon seller analytics assistant.

## Your Role
Answer metric questions by fetching live data and formatting responses clearly.

## Question Types You Handle
1. **Store Overview** ("how am I doing") → Request: ["total_sales", "net_profit", "roi"]
2. **Single Metric** ("what is my ACOS") → Extract metric name
3. **Domain Metrics** ("show me CFO metrics") → Request all domain metrics

## Available Metrics by Domain

**Advertising (14 metrics):**
ad_sales, ad_spend, acos, roas, cpc, ad_ctr, ad_cvr, ad_clicks, ad_impressions, ad_units_sold, ad_orders, time_in_budget, cac

**Total/Aggregate (18 metrics):**
total_sales, total_units_sold, total_spend, total_clicks, total_orders, cvr, tacos, mer, net_proceeds, ctr, cogs, monthly_budget, lost_sales, roi, contribution_margin, contribution_profit, gross_margin

**CFO/Financial (17 metrics):**
available_capital, frozen_capital, borrowed_capital, lost_sales, cost_of_goods_sold, gross_profit, net_profit, amazon_fees, misc, contribution_profit, gross_margin, contribution_margin, net_margin, opex, ebitda, roi

**Organic (9 metrics):**
organic_impressions, organic_clicks, organic_orders, organic_units_sold, organic_cvr, organic_ctr, organic_sales, organic_lost_sales, organic_add_to_cart

**Attribution (12 metrics):**
attribution_sales, attribution_spend, attribution_impressions, attribution_clicks, attribution_units_sold, attribution_orders, attribution_ctr, attribution_cvr, attribution_acos, attribution_roas, attribution_cpc, attribution_cpm

**Inventory (3 metrics):**
safety_stock, inventory_turnover, fba_in_stock_rate

## Process
1. Determine which metrics are needed
2. Call get_metrics tool with metric list
3. Format response with proper formatting

## Formatting Rules
- Currency: 1935035 → **$1,935,035**
- Percentage: 0.2656 → **26.56%**
- Always include date range: "(Sep 1-14, 2025)"

## Critical Rules
- ALWAYS call get_metrics (never make up numbers)
- Be concise (no preamble)
- Bold all values
- Include date range"""
Comparison Query Handler
pythondef compare_query_handler_node(state: AgentState) -> AgentState:
    """
    Handler for compare_query type questions.
    
    Handles questions like:
    - "Compare August vs September"
    - "How did sales change from Q1 to Q2?"
    
    NOTE: Currently a placeholder - full implementation needed
    """
    
    logger.info(f"💬 Processing compare_query: '{state['question']}'")
    
    settings = get_settings()
    
    # Define tool for comparison metrics
    @tool
    async def get_metrics_comparison(metrics: List[str]) -> dict:
        """Fetch metrics for TWO periods for comparison.
        
        Args:
            metrics: List of metric names to compare
            
        Returns:
            {
                "current": {...metrics for recent period...},
                "comparison": {...metrics for earlier period...}
            }
        """
        logger.info(f"🔧 Tool: get_metrics_comparison({metrics})")
        
        access_layer = MetricsAccessLayer()
        result = await access_layer.get_metrics_comparison(
            metrics,
            state["date_start"],
            state["date_end"],
            state["compare_date_start"],
            state["compare_date_end"]
        )
        
        logger.info(f"✓ Retrieved comparison data")
        return result
    
    # Create AI agent
    llm = ChatOpenAI(model=settings.openai_model, temperature=0)
    
    agent = create_react_agent(
        llm,
        tools=[get_metrics_comparison],
        state_modifier=COMPARISON_QUERY_SYSTEM_PROMPT
    )
    
    # Run agent
    logger.info("🤖 Running comparison query agent...")
    
    result = agent.invoke({
        "messages": [(
            "human",
            f"""Question: {state['question']}

Current period: {state['date_start']} to {state['date_end']}
Comparison period: {state['compare_date_start']} to {state['compare_date_end']}

Use get_metrics_comparison to fetch data for both periods and provide a comparison."""
        )]
    })
    
    state["response"] = result["messages"][-1].content
    logger.info(f"✓ Generated comparison response")
    
    return state

# System prompt for comparison query handler
COMPARISON_QUERY_SYSTEM_PROMPT = """You are an Amazon seller analytics assistant specialized in period comparisons.

## Your Role
Compare metrics between two time periods and highlight changes.

## Process
1. Determine which metrics to compare
2. Call get_metrics_comparison to get data for BOTH periods
3. Calculate changes (absolute and percentage)
4. Format comparison clearly

## Response Format
Always show:
- **Period 1 (earlier):** [formatted value]
- **Period 2 (recent):** [formatted value]
- **Change:** [absolute change] ([percentage change])

Example:
**August 2025:** $1,750,000
**September 2025:** $1,935,035
**Change:** +$185,035 (+10.6% increase)

## Formatting Rules
- Currency: Add $ and commas
- Percentage: Show with % sign
- Changes: Use + for increases, - for decreases
- Always include both period labels"""
ASIN Product Handler (Placeholder)
pythondef asin_product_handler_node(state: AgentState) -> AgentState:
    """
    Handler for asin_product type questions.
    
    Handles ASIN-specific questions like:
    - "What are sales for ASIN B0B5HN65QQ?"
    - "When will product B0DP55J8ZG go out of stock?"
    
    TODO: Implement ASIN-specific tools and logic
    """
    
    logger.info(f"💬 Processing asin_product query: '{state['question']}'")
    logger.info(f"📦 ASIN: {state.get('asin', 'N/A')}")
    logger.info(f"📅 Date: {state['date_start']} to {state['date_end']}")
    
    # Placeholder response
    state["response"] = f"""ASIN Product Handler (Coming Soon)

You asked about ASIN: {state.get('asin', 'Unknown')}
Date range: {state['date_start']} to {state['date_end']}

This handler will provide:
- ASIN-specific sales, units, revenue
- Inventory status and stockout predictions
- Product-level performance metrics
- Competitor comparisons for this ASIN

Implementation pending."""
    
    logger.info("⚠️  ASIN handler not yet implemented, returned placeholder")
    
    return state
Hardcoded Response Handler
pythondef hardcoded_response_node(state: AgentState) -> AgentState:
    """
    Handler for hardcoded responses (special questions).
    
    Handles:
    - Performance insights
    - Highest performance day
    - Other pre-defined responses
    """
    
    logger.info(f"💬 Processing hardcoded query: '{state['question']}'")
    
    question_lower = state['question'].lower()
    
    if "performance insight" in question_lower or "performance compare" in question_lower:
        state["response"] = """Performance Insights:

- Strongest improvement during Sep 01-05, 2025 (optimized ACOS to 20%)
- Net profit increased 9.2% from August to September (reduced TOS IS from 18% to 15%)

Optimization potential: You could have made $48,290 additional net profit (15% increase) from Aug 15 to Sep 30, 2025, if you had adjusted ACOS to 20% and TOS IS to 7-8%."""
    
    elif "highest performance" in question_lower:
        state["response"] = "Your highest performance day in September was Sep 2, 2025"
    
    else:
        state["response"] = "I'm not sure how to answer that question. Please try rephrasing."
    
    logger.info("✓ Returned hardcoded response")
    
    return state

Testing Strategy with LangSmith
Do You Still Need Tests with LangSmith?
YES! LangSmith is NOT a replacement for tests.
Here's why:
PurposeTestsLangSmithWhenDuring developmentAfter deploymentWhatVerify correctnessMonitor production behaviorAutomatedYes (CI/CD)No (manual inspection)Catch bugsBefore deploymentAfter users see themCostFreeCosts money per trace
What to Test vs What to Monitor
✅ Write Tests For:
1. Node Logic
python# tests/test_nodes.py
def test_classify_metrics_query():
    """Test that metrics queries are classified correctly"""
    state = {
        "question": "What is my ACOS?",
        "question_type": ""
    }
    
    result = classify_question_node(state)
    
    assert result["question_type"] == "metrics_query"

def test_classify_comparison_query():
    """Test that comparison queries are classified correctly"""
    state = {
        "question": "Compare August vs September",
        "question_type": ""
    }
    
    result = classify_question_node(state)
    
    assert result["question_type"] == "compare_query"

def test_extract_dates_single_period():
    """Test date extraction for single period"""
    state = {
        "question": "What was my ACOS yesterday?",
        "date_start": "",
        "date_end": ""
    }
    
    result = extract_dates_metrics_node(state)
    
    from datetime import datetime, timedelta
    expected_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    assert result["date_start"] == expected_date
    assert result["date_end"] == expected_date
2. Data Access Layer
python# tests/test_metrics_api.py
import pytest
from app.services.metrics_api import MetricsAccessLayer
from app.context import RequestContext

@pytest.mark.asyncio
async def test_get_metrics():
    """Test fetching metrics from API"""
    
    with RequestContext("test-jwt", is_dev=True, session_id="test"):
        layer = MetricsAccessLayer()
        
        result = await layer.get_metrics(
            ["acos", "total_sales"],
            "2025-09-01",
            "2025-09-14"
        )
        
        assert "acos" in result
        assert "total_sales" in result
        assert isinstance(result["acos"], (int, float))

@pytest.mark.asyncio
async def test_get_metrics_comparison():
    """Test comparison metrics"""
    
    with RequestContext("test-jwt", is_dev=True, session_id="test"):
        layer = MetricsAccessLayer()
        
        result = await layer.get_metrics_comparison(
            ["total_sales"],
            "2025-09-01", "2025-09-30",
            "2025-08-01", "2025-08-31"
        )
        
        assert "current" in result
        assert "comparison" in result
        assert "total_sales" in result["current"]
        assert "total_sales" in result["comparison"]
3. FastAPI Endpoints
python# tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_chatbot_endpoint_requires_jwt():
    """Test that endpoint requires JWT"""
    response = client.post(
        "/chatbot",
        json={
            "message": "What is my ACOS?",
            "sessionId": "test"
        }
    )
    assert response.status_code == 401

def test_chatbot_endpoint_success():
    """Test successful request"""
    response = client.post(
        "/chatbot",
        headers={"Authorization": "Bearer test-jwt"},
        json={
            "message": "What is my ACOS?",
            "sessionId": "test"
        }
    )
    assert response.status_code == 200
    assert "myField" in response.json()

def test_classifier_routes_correctly():
    """Test that different question types are handled"""
    
    # Test metrics query
    response = client.post(
        "/chatbot",
        headers={"Authorization": "Bearer test-jwt"},
        json={
            "message": "What is my ACOS?",
            "sessionId": "test"
        }
    )
    assert response.status_code == 200
    
    # Test comparison query
    response = client.post(
        "/chatbot",
        headers={"Authorization": "Bearer test-jwt"},
        json={
            "message": "Compare August vs September",
            "sessionId": "test"
        }
    )
    assert response.status_code == 200
4. Edge Cases
pythondef test_invalid_date_format():
    """Test handling of invalid dates"""
    state = {
        "question": "What was my ACOS on invalid-date?",
        "date_start": "",
        "date_end": ""
    }
    
    # Should not crash, should use default dates
    result = extract_dates_metrics_node(state)
    
    assert result["date_start"]  # Should have some valid date
    assert result["date_end"]

def test_empty_question():
    """Test handling of empty question"""
    state = {
        "question": "",
        "question_type": ""
    }
    
    result = classify_question_node(state)
    
    # Should default to metrics_query
    assert result["question_type"] == "metrics_query"
🔍 Use LangSmith For:
1. Monitoring Production
python# app/main.py (with LangSmith)
import os

# Enable tracing
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "amazon-seller-chatbot-prod"
os.environ["LANGCHAIN_API_KEY"] = "your-api-key"

# Now all LangGraph executions are automatically traced
2. Debugging Real User Issues

See exact LLM prompts and responses
See which tools were called
See the full state at each node
Track costs per request

3. A/B Testing Prompts

Compare different system prompts
See which gets better results
Track success rates

4. Finding Edge Cases in Production

See questions that failed
See questions that took too long
See unusual classification patterns

Recommended Testing Setup
python# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# .env.test
OPENAI_API_KEY=sk-test-...
DEV_API_BASE_URL=https://api0.dev.nyle.ai/math/v1
PROD_API_BASE_URL=https://api.nyle.ai/math/v1
REDIS_URL=redis://localhost:6379
ENABLE_TRACING=false  # Disable LangSmith for tests
bash# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run only fast tests (skip slow integration tests)
pytest tests/ -m "not integration"
Test Coverage Goals

Unit tests: 80%+ coverage

All node functions
All date extraction logic
All classification logic


Integration tests: Key flows

Metrics query end-to-end
Comparison query end-to-end
Error handling


API tests: All endpoints

Success cases
Error cases (401, 500)
Validation errors



Don't test:

LLM responses (too non-deterministic)
Exact response formatting (changes frequently)
Third-party API internals

Do test:

That correct APIs are called
That correct metrics are requested
That errors are handled gracefully
That routing works correctly


Summary
New Structure

5 total nodes (was 3)
1 classifier → routes to 4 paths
3 date extractors (one per question type)
3 handlers (metrics_query, compare_query, asin_product)
1 hardcoded response node

Testing Strategy

Write tests for business logic, API integration, edge cases
Use LangSmith for production monitoring, debugging, optimization
Don't replace tests with monitoring - they serve different purposes

Does this structure make sense now?Claude is AI and can make mistakes. Please double-check responses. Sonnet 4.5Claude is AI and can make mistakes. Please double-check responses.