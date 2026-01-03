"""
Comprehensive test for all Metrics APIs - Using MathMetricRetriever Methods

This test calls all 14 methods from metrics_api.py to get real data
from the Nyle math backend.

Configuration: Fill in JWT_TOKEN, ENVIRONMENT, and date range below.
Run with: python tests/test_all_metrics_apis.py
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
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY3NDU4MDE2LCJpYXQiOjE3NjczNzE2MTYsImp0aSI6IjBkZmM1ZDk4YThlMzQ0YTJiZTIyODg1YWViYTMzOTIwIiwic3ViIjoiNGY4OWJlOWUtZTljMS00M2YyLWI1NzMtNTVjNmNlZTM0NDQxIiwiaXNzIjoibnlsZS5haSJ9.ssXmgzkGajLgw3PqxZenurApLVqDjKTYpHKOSlvRvRE"

# 2. Environment (determines which base URL to use)
#    "dev" -> uses dev_base_url
#    "local" or "production" -> uses prod_base_url (api.nyle.ai)
ENVIRONMENT = "production"  # Using production URL: api.nyle.ai

# 3. Date Range
DATE_START = "2025-10-01"
DATE_END = "2025-10-31"

# 4. Optional ASIN for filtering
TEST_ASIN = None  # Set to an ASIN string like "B07YN9JXNW" to filter by ASIN

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
        
        # Display summary based on result type
        if isinstance(result, dict):
            # For data arrays, show count
            if "data" in result and isinstance(result["data"], list):
                data_points = result["data"]
                print(f"\nResponse: {len(data_points)} data points")
                if data_points:
                    print(f"\nFirst entry:")
                    print(json.dumps(data_points[0], indent=2))
            else:
                print(f"\nResponse (first 500 chars):")
                result_str = json.dumps(result, indent=2)
                print(result_str[:500] + ("..." if len(result_str) > 500 else ""))
        elif isinstance(result, (int, float)):
            print(f"\nResponse: {result}")
        else:
            print(f"\nResponse: {result}")
            
        return result
        
    except Exception as e:
        print(f"\n✗ FAILED")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_all_apis():
    """Test all 14 methods from metrics_api.py"""

    print("\n" + "🚀 " + "="*56 + " 🚀")
    print("   TESTING ALL MATH METRIC RETRIEVER APIs")
    print("   Calling all 14 Methods from metrics_api.py")
    print("🚀 " + "="*56 + " 🚀")
    
    settings = get_settings()
    
    print(f"\n📋 Configuration:")
    print(f"   Environment: {settings.environment}")
    print(f"   Dev Base URL: {settings.dev_base_url}")
    print(f"   Prod Base URL: {settings.prod_base_url}")
    print(f"   JWT Token: {JWT_TOKEN[:20]}..." if JWT_TOKEN else "   JWT Token: NOT SET!")
    print(f"   Date Range: {DATE_START} to {DATE_END}")
    if TEST_ASIN:
        print(f"   ASIN Filter: {TEST_ASIN}")
    
    if not JWT_TOKEN:
        print("\n⚠️  ERROR: JWT_TOKEN is not set!")
        print("Please set JWT_TOKEN at the top of this file.")
        return
    
    # Use RequestContext to inject JWT for all API calls
    with RequestContext(jwt_token=JWT_TOKEN, session_id="test-all-metrics-apis"):
        
        results = {}
        
        # API 1: Ads Executive Summary
        results["ads_executive_summary"] = await test_method(
            method_name="get_ads_executive_summary()",
            method_call=lambda: metrics_api.get_ads_executive_summary(
                date_start=DATE_START, 
                date_end=DATE_END, 
                asin=TEST_ASIN,
                saturation=0
            ),
            api_name="API 1: get_ads_executive_summary"
        )
        
        # API 2: Financial Summary
        results["financial_summary"] = await test_method(
            method_name="get_financial_summary()",
            method_call=lambda: metrics_api.get_financial_summary(
                date_start=DATE_START, 
                date_end=DATE_END,
                asin=TEST_ASIN
            ),
            api_name="API 2: get_financial_summary"
        )
        
        # API 3: Organic Metrics
        results["organic_metrics"] = await test_method(
            method_name="get_organic_metrics()",
            method_call=lambda: metrics_api.get_organic_metrics(
                date_start=DATE_START, 
                date_end=DATE_END
            ),
            api_name="API 3: get_organic_metrics"
        )
        
        # API 4: Inventory Status
        results["inventory_status"] = await test_method(
            method_name="get_inventory_status()",
            method_call=lambda: metrics_api.get_inventory_status(
                date_start=DATE_START, 
                date_end=DATE_END,
                asin=TEST_ASIN
            ),
            api_name="API 4: get_inventory_status"
        )
        
        # API 5: Attribution Metrics
        results["attribution_metrics"] = await test_method(
            method_name="get_attribution_metrics()",
            method_call=lambda: metrics_api.get_attribution_metrics(
                date_start=DATE_START, 
                date_end=DATE_END
            ),
            api_name="API 5: get_attribution_metrics"
        )
        
        # API 6: Total Metrics Summary
        results["total_metrics_summary"] = await test_method(
            method_name="get_total_metrics_summary()",
            method_call=lambda: metrics_api.get_total_metrics_summary(
                date_start=DATE_START,
                date_end=DATE_END,
                asin=TEST_ASIN
            ),
            api_name="API 6: get_total_metrics_summary"
        )
        
        # API 7: Combined Ads & Organic Keywords
        results["combined_keywords"] = await test_method(
            method_name="get_combined_ads_organic_keywords()",
            method_call=lambda: metrics_api.get_combined_ads_organic_keywords(
                date_start=DATE_START,
                date_end=DATE_END,
                sort_field="combined_sales",
                sort_direction="desc",
                offset=0,
                limit=10,
                asin=TEST_ASIN
            ),
            api_name="API 7: get_combined_ads_organic_keywords"
        )
        
        # API 8: Non-Optimal Ad Spends
        results["non_optimal_spends"] = await test_method(
            method_name="get_non_optimal_spends()",
            method_call=lambda: metrics_api.get_non_optimal_spends(
                date_start=DATE_START,
                date_end=DATE_END,
                asin=TEST_ASIN
            ),
            api_name="API 8: get_non_optimal_spends"
        )
        
        # API 9: Daily ACOS
        results["daily_acos"] = await test_method(
            method_name="get_daily_acos()",
            method_call=lambda: metrics_api.get_daily_acos(
                date_start=DATE_START,
                date_end=DATE_END,
                timespan="day",
                asin=TEST_ASIN
            ),
            api_name="API 9: get_daily_acos"
        )
        
        # API 10: Daily Ad TOS IS
        results["daily_ad_tos_is"] = await test_method(
            method_name="get_daily_ad_tos_is()",
            method_call=lambda: metrics_api.get_daily_ad_tos_is(
                date_start=DATE_START,
                date_end=DATE_END,
                timespan="day",
                asin=TEST_ASIN
            ),
            api_name="API 10: get_daily_ad_tos_is"
        )
        
        # API 11: Daily Total Sales
        results["daily_total_sales"] = await test_method(
            method_name="get_daily_total_sales()",
            method_call=lambda: metrics_api.get_daily_total_sales(
                date_start=DATE_START,
                date_end=DATE_END,
                timespan="day",
                asin=TEST_ASIN
            ),
            api_name="API 11: get_daily_total_sales"
        )
        
        # API 12: Daily Net Profit
        results["daily_net_profit"] = await test_method(
            method_name="get_daily_net_profit()",
            method_call=lambda: metrics_api.get_daily_net_profit(
                date_start=DATE_START,
                date_end=DATE_END,
                timespan="day",
                asin=TEST_ASIN
            ),
            api_name="API 12: get_daily_net_profit"
        )
        
        # API 13: Daily ROI
        results["daily_roi"] = await test_method(
            method_name="get_daily_roi()",
            method_call=lambda: metrics_api.get_daily_roi(
                date_start=DATE_START,
                date_end=DATE_END,
                timespan="day",
                asin=TEST_ASIN
            ),
            api_name="API 13: get_daily_roi"
        )
        
        # API 14: Optimal Goals
        results["optimal_goals"] = await test_method(
            method_name="get_optimal_goals()",
            method_call=lambda: metrics_api.get_optimal_goals(
                date_start=DATE_START,
                date_end=DATE_END,
                asin=TEST_ASIN
            ),
            api_name="API 14: get_optimal_goals"
        )
        
        # Summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        success_count = sum(1 for r in results.values() if r is not None)
        total_count = len(results)
        
        print(f"\nTotal: {total_count} APIs tested")
        print(f"Passed: {success_count}")
        print(f"Failed: {total_count - success_count}")
        
        if success_count == total_count:
            print("\n✅ ALL 14 APIs PASSED!")
        else:
            print(f"\n⚠️  {total_count - success_count} API(s) failed")
            print("\nFailed APIs:")
            for name, result in results.items():
                if result is None:
                    print(f"  ✗ {name}")


# ============================================================
# RUN THE TEST
# ============================================================

if __name__ == "__main__":
    asyncio.run(test_all_apis())

