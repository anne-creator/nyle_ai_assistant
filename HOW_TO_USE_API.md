# How to Use Metrics API

## Singleton Pattern Built-In

The singleton pattern is implemented **inside** the `MathMetricRetriever` class.  
Just import and use `metrics_api` - it's already a singleton!

## Simplest Usage

```python
from app.metricsAccessLayer import metrics_api
from app.context import RequestContext

# Set up context with JWT
with RequestContext(jwt_token="your-jwt-here", session_id="test"):
    
    # Call directly - no need to create instances!
    result = await metrics_api.get_financial_summary("2025-10-01", "2025-10-31")
    
    print(result)
```

## Available Functions

| Function | Endpoint | Returns |
|----------|----------|---------|
| `get_ads_executive_summary()` | `/math/ads/executive-summary` | Advertising metrics |
| `get_financial_summary()` | `/math/cfo/executive-summary` | CFO/financial metrics |
| `get_organic_metrics()` | `/math/organic/metrics` | Organic performance |
| `get_inventory_status()` | `/math/inventory/status` | Inventory data |
| `get_attribution_metrics()` | `/math/attribution/metrics` | Attribution metrics |
| `get_product_performance()` | `/math/products/{asin}/performance` | Product-specific data |

## Usage in Handler Tools

```python
from langchain_core.tools import tool
from app.metricsAccessLayer import metrics_api

@tool
async def get_financial_data(date_start: str, date_end: str) -> dict:
    """Fetch financial metrics."""
    return await metrics_api.get_financial_summary(date_start, date_end)
```

## Usage Anywhere in Your Project

```python
from app.metricsAccessLayer import metrics_api

async def my_function():
    result = await metrics_api.get_ads_executive_summary("2025-10-01", "2025-10-31")
    return result
```

## Why This is Better

**Old way (creating instances):**
```python
api = MathMetricRetriever()  # Create new instance
result = await api.get_financial_summary(...)
```

**New way (built-in singleton):**
```python
from app.metricsAccessLayer import metrics_api  # Already a singleton!
result = await metrics_api.get_financial_summary(...)
```

**Benefits:**
- ✅ Singleton pattern is hidden inside the class
- ✅ No separate `instance.py` file needed
- ✅ Cleaner imports
- ✅ More efficient

## Project Structure

```
app/metricsAccessLayer/
├── __init__.py                  # Exports metrics_api
├── math_metric_retriver.py      # All 6 APIs + singleton pattern
└── BaseAPIClient.py             # HTTP client
```

No `instance.py` needed - singleton is built-in!
