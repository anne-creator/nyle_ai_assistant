"""
Test for Metrics Access Layer - Using MathMetricRetriever Methods

This test calls all 6 methods from metrics_api.py to get real data
from the Nyle math backend.

Configuration: Fill in JWT_TOKEN, ENVIRONMENT, and date range below.
Run with: python tests/test_metrics_api.py
"""

import asyncio
import json
import os
import sys

# Add project root to path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ============================================================
# CONFIGURATION - FILL THESE IN!
# ============================================================

# 1. Your JWT Token
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY2Mzc4NzkyLCJpYXQiOjE3NjYzNzUxOTIsImp0aSI6IjkwYjhiZjEwZDA1YzQzOTY5ZjU4ZGE1YzdkMjBmNWFmIiwic3ViIjoiNGY4OWJlOWUtZTljMS00M2YyLWI1NzMtNTVjNmNlZTM0NDQxIiwic2NvcGVzIjoiIiwiYXVkIjpbImFwaSJdLCJpc3MiOiJueWxlLmFpIn0.8i52ItyI511Jaa7pCdqBfGwzAPsHp-o0hU2udfnyicw"

# 2. Environment (determines which base URL to use)
#    "dev" -> https://api0.dev.nyle.ai/math/v1
#    "local" or "production" -> https://api.nyle.ai/math/v1
ENVIRONMENT = "dev"  # Change to "local" or "production" to use prod URL

# 3. Date Range
DATE_START = "2025-10-01"
DATE_END = "2025-10-31"

# Set environment variable before importing app modules
os.environ["ENVIRONMENT"] = ENVIRONMENT

# Import the singleton metrics_api instance from metrics_api.py
from app.metricsAccessLayer.metrics_api import metrics_api
from app.context import RequestContext
from app.config import get_settings


# ============================================================
# TEST FUNCTIONS
# ============================================================

async def test_method(method_name: str, method_call, api_name: str):
    """Generic test wrapper for any metrics_api method"""
    
    print(f"\n{'='*60}")
    print(f"Testing: {api_name}")
    print(f"{'='*60}")
    print(f"Method: metrics_api.{method_name}")
    
    try:
        result = await method_call()
        
        print(f"\n✓ SUCCESS")
        print(f"\nResponse:")
        print(json.dumps(result, indent=2))
        return result
        
    except Exception as e:
        print(f"\n✗ FAILED")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_all_apis():
    """Test all 6 methods from metrics_api.py"""

    print("\n" + "🚀 " + "="*56 + " 🚀")
    print("   TESTING MATH METRIC RETRIEVER")
    print("   Calling 6 Methods from metrics_api.py")
    print("🚀 " + "="*56 + " 🚀")
    
    settings = get_settings()
    
    print(f"\n📋 Configuration:")
    print(f"   Environment: {settings.environment}")
    print(f"   Base URL: {settings.get_api_base_url()}")
    print(f"   JWT Token: {JWT_TOKEN[:20]}..." if JWT_TOKEN else "   JWT Token: NOT SET!")
    print(f"   Date Range: {DATE_START} to {DATE_END}")
    
    if not JWT_TOKEN:
        print("\n⚠️  ERROR: JWT_TOKEN is not set!")
        print("Please set JWT_TOKEN at the top of this file.")
        return
    
    # Use RequestContext to inject JWT for all API calls
    with RequestContext(jwt_token=JWT_TOKEN, session_id="test-metrics-api"):
        
        results = {}
        
        # Method 1: get_ads_executive_summary
        results["ads_summary"] = await test_method(
            method_name="get_ads_executive_summary()",
            method_call=lambda: metrics_api.get_ads_executive_summary(
                date_start=DATE_START, 
                date_end=DATE_END, 
                saturation=0
            ),
            api_name="Method 1: get_ads_executive_summary"
        )
        
        # Method 2: get_financial_summary
        results["financial_summary"] = await test_method(
            method_name="get_financial_summary()",
            method_call=lambda: metrics_api.get_financial_summary(
                date_start=DATE_START, 
                date_end=DATE_END
            ),
            api_name="Method 2: get_financial_summary"
        )
        
        # Method 3: get_organic_metrics
        results["organic_metrics"] = await test_method(
            method_name="get_organic_metrics()",
            method_call=lambda: metrics_api.get_organic_metrics(
                date_start=DATE_START, 
                date_end=DATE_END
            ),
            api_name="Method 3: get_organic_metrics"
        )
        
        # Method 4: get_inventory_status
        results["inventory"] = await test_method(
            method_name="get_inventory_status()",
            method_call=lambda: metrics_api.get_inventory_status(
                date_start=DATE_START, 
                date_end=DATE_END
            ),
            api_name="Method 4: get_inventory_status"
        )
        
        # Method 5: get_attribution_metrics
        results["attribution"] = await test_method(
            method_name="get_attribution_metrics()",
            method_call=lambda: metrics_api.get_attribution_metrics(
                date_start=DATE_START, 
                date_end=DATE_END
            ),
            api_name="Method 5: get_attribution_metrics"
        )
        
        # Method 6: get_total_metrics_summary
        results["total_metrics_summary"] = await test_method(
            method_name="get_total_metrics_summary()",
            method_call=lambda: metrics_api.get_total_metrics_summary(
                date_start=DATE_START, 
                date_end=DATE_END
            ),
            api_name="Method 6: get_total_metrics_summary"
        )
        
        # Summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        success_count = sum(1 for r in results.values() if r is not None)
        total_count = len(results)
        
        print(f"\nTotal: {total_count} methods tested")
        print(f"Passed: {success_count}")
        print(f"Failed: {total_count - success_count}")
        
        if success_count == total_count:
            print("\n✅ ALL 6 METHODS PASSED!")
        else:
            print(f"\n⚠️  {total_count - success_count} method(s) failed")


# ============================================================
# RUN THE TEST
# ============================================================

if __name__ == "__main__":
    asyncio.run(test_all_apis())
