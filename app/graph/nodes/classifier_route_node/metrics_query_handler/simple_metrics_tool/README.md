# Simple Metrics Tool - AI Agent

## Overview

The Simple Metrics Tool is an intelligent AI agent that retrieves specific metrics from multiple Nyle backend API endpoints. It mimics the n8n workflow structure and acts as a sub-agent within the metrics_query_handler system.

## Architecture

```
simple_metrics_tool/
├── __init__.py          # Package exports
├── tool.py              # Main agent implementation with 6 API tools
├── prompt.py            # System prompt for the AI agent
└── README.md            # This file
```

## How It Works

### 1. Input
The tool accepts three parameters:
- `metric_list`: List of metric names (e.g., `['acos', 'total_sales', 'net_profit']`)
- `date_start`: Start date in YYYY-MM-DD format
- `date_end`: End date in YYYY-MM-DD format

### 2. Process
1. **Analyze Request**: The AI agent analyzes which metrics are requested
2. **Route to APIs**: Determines which of the 6 API endpoints to call
3. **Fetch Data**: Calls only the necessary endpoints
4. **Extract**: Extracts only the requested metrics from the responses
5. **Format**: Returns a clean JSON with just the requested metrics

### 3. Output
Returns a structured JSON:
```json
{
  "status": "success",
  "metrics": {
    "acos": 0.2656,
    "total_sales": 1935035,
    "net_profit": 313828
  },
  "message": "Successfully retrieved 3 metrics"
}
```

## Six API Tools

The agent has access to 6 tools, each calling a different Nyle backend API:

### 1. GET_ads_executive_summary
**Endpoint**: `/math/ads/executive-summary`

**Returns**: ad_sales, ad_spend, ad_clicks, ad_impressions, ad_units_sold, ad_orders, acos, roas, cpc, cac, ad_ctr, ad_cvr, time_in_budget

### 2. GET_total_executive_summary
**Endpoint**: `/math/total/executive-summary`

**Returns**: total_sales, total_spend, total_impressions, ctr, total_clicks, cvr, total_orders, total_units_sold, total_ntb_orders, tacos, mer, lost_sales

### 3. GET_cfo_executive_summary
**Endpoint**: `/math/cfo/executive-summary`

**Returns**: available_capital, frozen_capital, borrowed_capital, lost_sales, cost_of_goods_sold, gross_profit, net_profit, amazon_fees, misc, contribution_profit, gross_margin, contribution_margin, net_margin, opex, ebitda, roi

### 4. GET_organic_executive_summary
**Endpoint**: `/math/organic/executive-summary`

**Returns**: organic_impressions, organic_clicks, organic_orders, organic_units_sold, organic_cvr, organic_ctr, organic_sales, organic_lost_sales, organic_add_to_cart (+ _what_if variants)

### 5. GET_attribution_executive_summary
**Endpoint**: `/math/attribution/executive-summary`

**Returns**: attribution_sales, attribution_spend, attribution_impressions, attribution_clicks, attribution_units_sold, attribution_orders, attribution_ctr, attribution_cvr, attribution_acos, attribution_roas, attribution_cpc, attribution_cpm, attribution_add_to_cart

### 6. GET_inventory_metrics_executive_summary
**Endpoint**: `/math/inventory/metrics/executive-summary`

**Returns**: safety_stock, inventory_turnover, fba_in_stock_rate

## Usage

The tool is automatically available to the parent `metrics_query_handler_node` agent. The parent agent can call it like:

```python
# The parent agent will invoke this tool with:
get_simple_metrics(
    metric_list=['acos', 'total_sales', 'net_profit'],
    date_start='2025-09-01',
    date_end='2025-09-14'
)
```

## Key Features

- **Intelligent Routing**: Only calls the API endpoints that contain the requested metrics
- **Efficient**: Minimizes API calls by determining the optimal set of endpoints
- **Structured Output**: Returns clean JSON with only requested metrics
- **Error Handling**: Gracefully handles errors and returns status information
- **Logging**: Comprehensive logging for debugging and monitoring

## Integration

The tool is integrated into the metrics_query_handler node at:
`app/graph/nodes/metrics_query_handler/node.py`

It appears in the tools list alongside other metric retrieval tools:
```python
tools=[get_ads_metrics, get_financial_metrics, get_simple_metrics]
```

## Dependencies

- **LangChain**: For AI agent framework
- **OpenAI**: For the language model (GPT-4.1)
- **Pydantic**: For input/output validation
- **metrics_api**: Singleton instance from `app.metricsAccessLayer`

## Configuration

The tool uses configuration from `app.config`:
- OpenAI API key
- OpenAI model selection
- Backend API base URL (from context)
- JWT authentication (from context)


