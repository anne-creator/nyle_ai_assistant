"""
Simple API Usage - Singleton Pattern Built-In

Usage:
    from app.metricsAccessLayer import metrics_api
    result = await metrics_api.get_financial_summary(date_start, date_end)
"""

import asyncio
from app.metricsAccessLayer import metrics_api
from app.context import RequestContext


async def summary(date_start: str, date_end: str) -> dict:
    """
    Get CFO executive summary metrics.
    
    Singleton is built into metrics_api - no need to create instances!
    
    Args:
        date_start: Start date (YYYY-MM-DD)
        date_end: End date (YYYY-MM-DD)
        
    Returns:
        Dict with financial metrics from /math/cfo/executive-summary
    """
    return await metrics_api.get_financial_summary(date_start, date_end)


async def main():
    """Example usage."""
    
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY2Mzc0NjcyLCJpYXQiOjE3NjYzNzEwNzIsImp0aSI6ImZhYTk3YmQzOWJjYjRiOWNiY2QxNDRiZmY5Y2YzMTdjIiwic3ViIjoiNGY4OWJlOWUtZTljMS00M2YyLWI1NzMtNTVjNmNlZTM0NDQxIiwic2NvcGVzIjoiIiwiYXVkIjpbImFwaSJdLCJpc3MiOiJueWxlLmFpIn0.cMUh1wAMcctTz8CXpmh_7Uxa6g3IXqMG6meBfuP0JQI"
    
    with RequestContext(jwt_token=jwt_token, session_id="example"):
        # Call your function
        result = await summary("2025-10-01", "2025-10-31")
        
        print("Got metrics:")
        print(result)


if __name__ == "__main__":
    print("Simple API Call - Singleton Pattern Built-In")
    print("-" * 50)
    asyncio.run(main())
