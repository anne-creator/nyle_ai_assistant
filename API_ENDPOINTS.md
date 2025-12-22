# Nyle Backend API Endpoints

This document lists all available Nyle backend APIs and how to use them.

## Base URLs

| Environment | Base URL |
|-------------|----------|
| Local | `https://api.nyle.ai/math/v1` |
| Dev | `https://api0.dev.nyle.ai/math/v1` |
| Production | `https://api.nyle.ai/math/v1` |

## Available APIs

### 1. Ads Executive Summary

**Method:** `NyleBackendAPI.get_ads_executive_summary()`

```python
api = NyleBackendAPI()
result = await api.get_ads_executive_summary(
    date_start="2025-10-01",
    date_end="2025-10-03",
    saturation=0  # optional, default=0
)
```

**Endpoint:** `GET /math/ads/executive-summary`

**Query Params:**
- `date_start` (required): YYYY-MM-DD
- `date_end` (required): YYYY-MM-DD
- `saturation` (optional): int, default 0

---

### 2. Financial Summary

**Method:** `NyleBackendAPI.get_financial_summary()`

```python
result = await api.get_financial_summary(
    date_start="2025-10-01",
    date_end="2025-10-03"
)
```

**Endpoint:** `GET /math/financial/summary`

---

### 3. Organic Metrics

**Method:** `NyleBackendAPI.get_organic_metrics()`

```python
result = await api.get_organic_metrics(
    date_start="2025-10-01",
    date_end="2025-10-03"
)
```

**Endpoint:** `GET /math/organic/metrics`

---

### 4. Inventory Status

**Method:** `NyleBackendAPI.get_inventory_status()`

```python
result = await api.get_inventory_status(
    date_start="2025-10-01",
    date_end="2025-10-03",
    asin="B0B5HN65QQ"  # optional
)
```

**Endpoint:** `GET /math/inventory/status`

**Query Params:**
- `asin` (optional): Filter by specific product

---

### 5. Attribution Metrics

**Method:** `NyleBackendAPI.get_attribution_metrics()`

```python
result = await api.get_attribution_metrics(
    date_start="2025-10-01",
    date_end="2025-10-03"
)
```

**Endpoint:** `GET /math/attribution/metrics`

---

### 6. Product Performance (ASIN-specific)

**Method:** `NyleBackendAPI.get_product_performance()`

```python
result = await api.get_product_performance(
    date_start="2025-10-01",
    date_end="2025-10-03",
    asin="B0B5HN65QQ"
)
```

**Endpoint:** `GET /math/products/{asin}/performance`

---

## Usage in Handler Tools

```python
from langchain_core.tools import tool
from app.api.nyle_backend import NyleBackendAPI

@tool
async def get_advertising_summary(date_start: str, date_end: str) -> dict:
    """Fetch advertising metrics."""
    api = NyleBackendAPI()
    return await api.get_ads_executive_summary(date_start, date_end)

# Use in create_react_agent()
agent = create_react_agent(
    llm,
    tools=[get_advertising_summary],
    prompt=SYSTEM_PROMPT
)
```

## Authentication

JWT authentication is handled automatically via `RequestContext`. The API client retrieves the JWT from context and includes it in the Authorization header.

## Error Handling

All methods will raise `httpx.HTTPStatusError` if the API returns an error. Handle these in your tools:

```python
@tool
async def safe_get_ads(date_start: str, date_end: str) -> dict:
    """Fetch ads with error handling."""
    try:
        api = NyleBackendAPI()
        return await api.get_ads_executive_summary(date_start, date_end)
    except Exception as e:
        return {"error": str(e)}
```

## Adding New Endpoints

To add a new endpoint:

1. Add a method to `NyleBackendAPI` in `app/api/nyle_backend.py`
2. Follow the existing pattern:
   - Async method
   - Clear docstring with args/returns
   - Use `self.client.get()` or `self.client.post()`
   - Log the request
3. Update this documentation

