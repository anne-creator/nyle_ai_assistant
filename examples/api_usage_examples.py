"""
Examples: How to Use Nyle API Retrievers

This shows different ways to call the API functions throughout your project.
"""

import asyncio
from app.api.nyle_api import NyleAPI
from app.context import RequestContext


# ============================================================
# Example 1: Direct Usage (Simplest)
# ============================================================

async def simple_usage():
    """Most basic way to get financial summary."""
    
    # You need JWT from somewhere (from request in production)
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    
    # Set up context with JWT
    with RequestContext(jwt_token=jwt_token, session_id="test"):
        
        # Create API instance
        api = NyleAPI()
        
        # Call the function - it's that simple!
        result = await api.get_financial_summary("2025-10-01", "2025-10-31")
        
        print(f"Financial data: {result}")
        return result


# ============================================================
# Example 2: In a Handler Tool (Most Common)
# ============================================================

from langchain_core.tools import tool

@tool
async def get_cfo_metrics(date_start: str, date_end: str) -> dict:
    """
    Fetch CFO metrics from Nyle backend.
    
    This tool can be called by the LLM agent.
    
    Args:
        date_start: Start date YYYY-MM-DD
        date_end: End date YYYY-MM-DD
        
    Returns:
        Dict with CFO metrics
    """
    api = NyleAPI()
    return await api.get_financial_summary(date_start, date_end)


# Usage in handler node:
def example_handler_usage():
    """How to use the tool in a handler node."""
    from langchain_openai import ChatOpenAI
    from langgraph.prebuilt import create_react_agent
    
    llm = ChatOpenAI(model="gpt-4o-mini")
    
    # Give the tool to the agent
    agent = create_react_agent(
        llm,
        tools=[get_cfo_metrics],  # ← Your tool here
        prompt="You are a financial analyst. Use get_cfo_metrics to answer questions."
    )
    
    # Agent can now call your API!
    result = agent.invoke({
        "messages": [("human", "What was my profit in October?")]
    })
    
    return result


# ============================================================
# Example 3: Wrapper Function (For Convenience)
# ============================================================

async def summary(date_start: str, date_end: str) -> dict:
    """
    Simple wrapper - just call this anywhere in your project.
    
    Usage:
        result = await summary("2025-10-01", "2025-10-31")
    """
    api = NyleAPI()
    return await api.get_financial_summary(date_start, date_end)


# ============================================================
# Example 4: In a FastAPI Endpoint (If You Need It)
# ============================================================

from fastapi import APIRouter, Header

router = APIRouter()

@router.get("/internal/summary")
async def get_summary_endpoint(
    date_start: str,
    date_end: str,
    authorization: str = Header(None)
):
    """
    Internal endpoint to get summary data.
    
    Usage:
        GET /internal/summary?date_start=2025-10-01&date_end=2025-10-31
    """
    jwt_token = authorization.replace("Bearer ", "")
    
    with RequestContext(jwt_token=jwt_token, session_id="internal"):
        api = NyleAPI()
        result = await api.get_financial_summary(date_start, date_end)
        return result


# ============================================================
# Example 5: Multiple APIs in One Call
# ============================================================

async def get_complete_overview(date_start: str, date_end: str) -> dict:
    """
    Get data from multiple APIs at once.
    
    Usage:
        overview = await get_complete_overview("2025-10-01", "2025-10-31")
    """
    api = NyleAPI()
    
    # Call multiple endpoints
    financial = await api.get_financial_summary(date_start, date_end)
    ads = await api.get_ads_executive_summary(date_start, date_end)
    organic = await api.get_organic_metrics(date_start, date_end)
    
    # Combine results
    return {
        "financial": financial,
        "advertising": ads,
        "organic": organic
    }


# ============================================================
# Example 6: With Error Handling
# ============================================================

async def safe_summary(date_start: str, date_end: str) -> dict:
    """
    Get summary with error handling.
    
    Returns error dict if something goes wrong.
    """
    try:
        api = NyleAPI()
        result = await api.get_financial_summary(date_start, date_end)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# Run Examples
# ============================================================

async def run_all_examples():
    """Run all examples (with fake JWT for demo)."""
    
    fake_jwt = "fake-jwt-token-for-demo"
    
    with RequestContext(jwt_token=fake_jwt, session_id="demo"):
        print("\n=== Example 1: Simple Usage ===")
        # result = await simple_usage()
        
        print("\n=== Example 3: Wrapper Function ===")
        # result = await summary("2025-10-01", "2025-10-31")
        # print(f"Result: {result}")
        
        print("\n=== Example 5: Complete Overview ===")
        # overview = await get_complete_overview("2025-10-01", "2025-10-31")
        # print(f"Overview: {overview}")
        
        print("\n=== Example 6: With Error Handling ===")
        result = await safe_summary("2025-10-01", "2025-10-31")
        print(f"Safe result: {result}")


if __name__ == "__main__":
    print("=" * 60)
    print("Nyle API Usage Examples")
    print("=" * 60)
    
    asyncio.run(run_all_examples())

