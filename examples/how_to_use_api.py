"""
Example: How to Use the Nyle Backend API Data Access Layer

This shows how to use NyleBackendAPI in your handler tools.
"""

import asyncio
from app.api.nyle_backend import NyleBackendAPI
from app.context import RequestContext


async def example_usage():
    """Example of using NyleBackendAPI in a handler tool."""
    
    # JWT token would come from the request in production
    # Here we use a fake one for demonstration
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    
    # Set up the request context (this happens automatically in main.py)
    with RequestContext(jwt_token=jwt_token, session_id="example"):
        
        # Initialize the API
        api = NyleBackendAPI()
        
        # Example 1: Get ads executive summary
        print("\n1. Fetching ads executive summary...")
        ads_summary = await api.get_ads_executive_summary(
            date_start="2025-10-01",
            date_end="2025-10-03",
            saturation=0
        )
        print(f"Result: {ads_summary}")
        
        # Example 2: Get financial summary
        print("\n2. Fetching financial summary...")
        financial = await api.get_financial_summary(
            date_start="2025-10-01",
            date_end="2025-10-03"
        )
        print(f"Result: {financial}")
        
        # Example 3: Get product performance
        print("\n3. Fetching product performance...")
        product_perf = await api.get_product_performance(
            date_start="2025-10-01",
            date_end="2025-10-03",
            asin="B0B5HN65QQ"
        )
        print(f"Result: {product_perf}")


async def example_in_handler_tool():
    """
    Example: How to use NyleBackendAPI inside a handler tool.
    
    This is the pattern you'll use in your actual handlers.
    """
    from langchain_core.tools import tool
    
    @tool
    async def get_ads_metrics(date_start: str, date_end: str) -> dict:
        """Fetch advertising metrics from Nyle backend.
        
        Args:
            date_start: Start date (YYYY-MM-DD)
            date_end: End date (YYYY-MM-DD)
            
        Returns:
            Dictionary with ads metrics
        """
        # Initialize API (JWT automatically retrieved from context)
        api = NyleBackendAPI()
        
        # Call the endpoint
        result = await api.get_ads_executive_summary(date_start, date_end)
        
        # Return the data
        return result
    
    # Tool is now ready to be used by create_react_agent()
    print("Tool created successfully!")


if __name__ == "__main__":
    print("=== Nyle Backend API Usage Examples ===")
    
    # Run the examples
    # asyncio.run(example_usage())
    asyncio.run(example_in_handler_tool())

