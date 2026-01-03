"""
Test for Products Access Layer - Using ProductsAPIClient Methods

This test calls all methods from products_api.py to get real data
from the Nyle Amazon backend.

Configuration: Fill in JWT_TOKEN and ENVIRONMENT below.
Run with: python tests/test_products_api.py
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

# 3. Test ASIN (for get_product_details)
TEST_ASIN = "B07YN9JXNW"  # Change to a valid ASIN from your account

# Set environment variable before importing app modules
os.environ["ENVIRONMENT"] = ENVIRONMENT

# Import the singleton products_api instance from products_api.py
from app.metricsAccessLayer.products_api import products_api
from app.context import RequestContext
from app.config import get_settings


# ============================================================
# TEST FUNCTIONS
# ============================================================

async def test_method(method_name: str, method_call, api_name: str):
    """Generic test wrapper for any products_api method"""
    
    print(f"\n{'='*60}")
    print(f"Testing: {api_name}")
    print(f"{'='*60}")
    print(f"Method: products_api.{method_name}")
    
    try:
        result = await method_call()
        
        print(f"\n✓ SUCCESS")
        
        # Display summary based on result type
        if isinstance(result, list):
            print(f"\nResponse: List with {len(result)} items")
            if result:
                print(f"\nFirst item:")
                print(json.dumps(result[0], indent=2))
                if len(result) > 1:
                    print(f"\n... and {len(result) - 1} more items")
        elif isinstance(result, dict):
            print(f"\nResponse:")
            print(json.dumps(result, indent=2))
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
    """Test all methods from products_api.py"""

    print("\n" + "🚀 " + "="*56 + " 🚀")
    print("   TESTING PRODUCTS API CLIENT")
    print("   Calling Methods from products_api.py")
    print("🚀 " + "="*56 + " 🚀")
    
    settings = get_settings()
    
    print(f"\n📋 Configuration:")
    print(f"   Environment: {settings.environment}")
    print(f"   Dev Base URL: {settings.dev_base_url}")
    print(f"   Prod Base URL: {settings.prod_base_url}")
    print(f"   JWT Token: {JWT_TOKEN[:20]}..." if JWT_TOKEN else "   JWT Token: NOT SET!")
    print(f"   Test ASIN: {TEST_ASIN}")
    
    if not JWT_TOKEN:
        print("\n⚠️  ERROR: JWT_TOKEN is not set!")
        print("Please set JWT_TOKEN at the top of this file.")
        return
    
    # Use RequestContext to inject JWT for all API calls
    with RequestContext(jwt_token=JWT_TOKEN, session_id="test-products-api"):
        
        results = {}
        
        # Method 1: get_ranked_products
        results["ranked_products"] = await test_method(
            method_name="get_ranked_products()",
            method_call=lambda: products_api.get_ranked_products(
                offset=0,
                limit=5,
                order_direction=1,
                order_by="executive_summary.total_sales"
            ),
            api_name="Method 1: get_ranked_products"
        )
        
        # Method 2: get_product_details
        results["product_details"] = await test_method(
            method_name="get_product_details()",
            method_call=lambda: products_api.get_product_details(TEST_ASIN),
            api_name=f"Method 2: get_product_details (ASIN: {TEST_ASIN})"
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
            print("\n✅ ALL METHODS PASSED!")
        else:
            print(f"\n⚠️  {total_count - success_count} method(s) failed")
        
        # Additional test: Test with different parameters
        print("\n" + "="*60)
        print("📋 ADDITIONAL TESTS")
        print("="*60)
        
        # Test get_ranked_products with different parameters
        print("\nTesting get_ranked_products with limit=3, order_direction=0 (ascending)...")
        try:
            result = await products_api.get_ranked_products(
                offset=0,
                limit=3,
                order_direction=0,  # ascending
                order_by="executive_summary.total_sales"
            )
            print(f"✓ Success: Received {len(result)} products")
        except Exception as e:
            print(f"✗ Failed: {str(e)}")


# ============================================================
# RUN THE TEST
# ============================================================

if __name__ == "__main__":
    asyncio.run(test_all_apis())

