"""
Test script for the 5 new daily metrics API methods.

Usage:
    python test_daily_metrics.py <date_start> <date_end> [asin]

Example:
    python test_daily_metrics.py 2025-10-01 2025-10-31
    python test_daily_metrics.py 2025-10-01 2025-10-31 B07YN9JXNW
"""

import asyncio
import sys
import json
from datetime import datetime

# Setup path for imports
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configuration
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY3NDU4MDE2LCJpYXQiOjE3NjczNzE2MTYsImp0aSI6IjBkZmM1ZDk4YThlMzQ0YTJiZTIyODg1YWViYTMzOTIwIiwic3ViIjoiNGY4OWJlOWUtZTljMS00M2YyLWI1NzMtNTVjNmNlZTM0NDQxIiwiaXNzIjoibnlsZS5haSJ9.ssXmgzkGajLgw3PqxZenurApLVqDjKTYpHKOSlvRvRE"
ENVIRONMENT = "production"  # Use production URL: api.nyle.ai

# Set environment before importing
os.environ["ENVIRONMENT"] = ENVIRONMENT

from app.metricsAccessLayer.metrics_api import metrics_api
from app.context import RequestContext


async def test_daily_metrics(date_start: str, date_end: str, asin: str = None):
    """Test all 5 daily metric endpoints."""
    
    print("=" * 80)
    print(f"Testing Daily Metrics APIs")
    print(f"Period: {date_start} to {date_end}")
    if asin:
        print(f"ASIN: {asin}")
    print("=" * 80)
    print()
    
    # Test each endpoint individually
    tests = [
        ("Daily ACOS", metrics_api.get_daily_acos),
        ("Daily Ad TOS IS", metrics_api.get_daily_ad_tos_is),
        ("Daily Total Sales", metrics_api.get_daily_total_sales),
        ("Daily Net Profit", metrics_api.get_daily_net_profit),
        ("Daily ROI", metrics_api.get_daily_roi),
    ]
    
    results = {}
    
    for name, method in tests:
        print(f"Testing: {name}")
        print("-" * 80)
        try:
            result = await method(date_start, date_end, timespan="day", asin=asin)
            
            # Display summary
            if isinstance(result, dict):
                data_points = result.get("data", [])
                print(f"✓ Success: Received {len(data_points)} data points")
                
                # Show first 3 and last 3 entries if available
                if data_points:
                    print(f"\nFirst entry:")
                    print(f"  {json.dumps(data_points[0], indent=2)}")
                    
                    if len(data_points) > 1:
                        print(f"\nLast entry:")
                        print(f"  {json.dumps(data_points[-1], indent=2)}")
                    
                    # Calculate some basic stats
                    values = [d.get("value", 0) for d in data_points if d.get("value") is not None]
                    if values:
                        avg = sum(values) / len(values)
                        print(f"\nStats:")
                        print(f"  Min: {min(values):.4f}")
                        print(f"  Max: {max(values):.4f}")
                        print(f"  Avg: {avg:.4f}")
                
                results[name] = {"status": "success", "count": len(data_points)}
            else:
                print(f"✓ Received: {result}")
                results[name] = {"status": "success", "result": str(result)}
                
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            results[name] = {"status": "error", "error": str(e)}
        
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for name, result in results.items():
        status = result["status"]
        if status == "success":
            count = result.get("count", "N/A")
            print(f"✓ {name}: {status.upper()} ({count} data points)")
        else:
            print(f"✗ {name}: {status.upper()} - {result.get('error', 'Unknown error')}")
    print()
    
    # Test parallel fetch (simulating trend_metrics_fetcher)
    print("=" * 80)
    print("Testing Parallel Fetch (all 5 at once)")
    print("=" * 80)
    try:
        start_time = datetime.now()
        
        results_parallel = await asyncio.gather(
            metrics_api.get_daily_acos(date_start, date_end, "day", asin),
            metrics_api.get_daily_ad_tos_is(date_start, date_end, "day", asin),
            metrics_api.get_daily_total_sales(date_start, date_end, "day", asin),
            metrics_api.get_daily_net_profit(date_start, date_end, "day", asin),
            metrics_api.get_daily_roi(date_start, date_end, "day", asin),
            return_exceptions=True
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"✓ All 5 APIs completed in parallel")
        print(f"  Duration: {duration:.2f} seconds")
        print(f"  Results:")
        for i, (name, _) in enumerate(tests):
            result = results_parallel[i]
            if isinstance(result, Exception):
                print(f"    ✗ {name}: {str(result)}")
            elif isinstance(result, dict):
                count = len(result.get("data", []))
                print(f"    ✓ {name}: {count} data points")
            else:
                print(f"    ✓ {name}: {result}")
    except Exception as e:
        print(f"✗ Parallel fetch failed: {str(e)}")


async def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    date_start = sys.argv[1]
    date_end = sys.argv[2]
    asin = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Validate date format
    try:
        datetime.strptime(date_start, "%Y-%m-%d")
        datetime.strptime(date_end, "%Y-%m-%d")
    except ValueError:
        print("Error: Dates must be in YYYY-MM-DD format")
        sys.exit(1)
    
    # Check JWT token
    if not JWT_TOKEN:
        print("Error: JWT_TOKEN not configured in test script")
        print("Please update JWT_TOKEN variable at the top of this file.")
        sys.exit(1)
    
    print(f"Using environment: {ENVIRONMENT}")
    print(f"JWT token: {JWT_TOKEN[:20]}...\n")
    
    # Run tests with RequestContext for authentication
    with RequestContext(jwt_token=JWT_TOKEN, session_id="test-daily-metrics"):
        await test_daily_metrics(date_start, date_end, asin)


if __name__ == "__main__":
    asyncio.run(main())

