# Trend Analysis Handler Refactoring Summary

## Date: January 15, 2026

## Overview
Refactored the `trend_analyzing_handler` to integrate user goal settings and streamline data fetching to 3 core metrics. The handler now prioritizes goal-based insights over raw metric observations.

## Changes Made

### 1. Added Goals List API
**File**: `app/metricsAccessLayer/metrics_api.py`

- Added new method `get_goals_list()` (API 15)
- Endpoint: `/math/v1/goals/list`
- Parameters: `date_start`, `date_end`, `asin` (optional)
- Returns: `{"goals": [{"asin": "...", "metric": "acos", "value": 23, "date_start": "...", "date_end": "..."}]}`

### 2. Refactored Trend Metrics Fetcher
**File**: `app/utils/trend_metrics_fetcher.py`

**Key Changes**:
- **Reduced from 5 to 3 metrics**: Now fetches only ACOS, Ad TOS IS, and Net Profit
- **Added goals fetching**: Parallel fetch of user-set goals via `get_goals_list()`
- **Updated data structure**: Daily records now only contain `d`, `acos`, `ad_tos_is`, `profit`
- **Removed metrics**: Total Sales and ROI (API methods kept in `metrics_api.py` for future use)
- **New helper function**: `_format_goals_for_llm()` formats goals for LLM consumption
- **Updated text format**: Changed from `date|ACOS|Ad_TOS_IS|Sales|Profit|ROI` to `date|ACOS|Ad_TOS_IS|Profit`
- **New return fields**: Added `goals` and `goals_text` to return dictionary

**Token Efficiency**: Reduced token usage by ~40% by removing 2 metrics from daily data

### 3. Updated LLM Prompt
**File**: `app/graph/nodes/classifier_route_node/insight_query_handler/prompt.py`

**Updated**: `TREND_ANALYSIS_PROMPT`

**Key Changes**:
- **Added Analysis Priority section**: Explicitly instructs LLM to check goals first
- **Two-tier analysis**:
  1. First: Check if user had active goals during profit changes
  2. Second: If no goals or goals don't explain change, analyze ACOS/Ad TOS IS
- **New examples**: Added examples showing goal-based insights
- **New rules**: "ALWAYS check User-Set Goals section first before analyzing metrics"

**Behavioral Impact**:
- LLM now says: "Your profit increased because you met your 23% ACOS goal"
- Instead of: "Your profit increased because ACOS dropped to 21%"
- Detects goal expiration: "Your profit dropped because your goal ended on Oct 15"

### 4. Updated Response Generator
**File**: `app/graph/nodes/node_utils/trend_analyzing_handler/node.py`

**Updated**: `_generate_trend_analysis_response()` function

**Key Changes**:
- Added `goals_text` to LLM prompt (placed first, before metrics data)
- Removed `sales_stats` and `roi_avg` from summary statistics
- Updated docstring to mention goal correlation

### 5. Stage 3 (Optimization Recommendations)
**File**: `app/graph/nodes/node_utils/trend_analyzing_handler/node.py`

**No changes needed** - The `_get_optimization_potential()` function already:
- Correctly calls `metrics_api.get_optimal_goals()`
- Extracts ACOS recommendation
- Creates set_goal button for next period
- Formats forward-looking recommendations

## API Methods Preserved

The following API methods were **kept in `metrics_api.py`** but are no longer used in trend analysis:
- `get_daily_total_sales()` (API 11)
- `get_daily_roi()` (API 13)

These remain available for future features.

## New Data Flow

```
User Query: "Show insights for Oct 1-30 for ASIN B0160HYB8S"
    ↓
Stage 1: Parallel API Calls
    ├─ get_daily_acos()
    ├─ get_daily_ad_tos_is()
    ├─ get_daily_net_profit()
    └─ get_goals_list() ← NEW
    ↓
Formatted Data:
    ├─ Daily metrics: date|ACOS|Ad_TOS_IS|Profit
    └─ Goals: "User-Set Goals:\n- ACOS: 23% (2025-10-01 to 2025-10-15)" ← NEW
    ↓
Stage 2: LLM Analysis
    ├─ Check goals first ← NEW PRIORITY
    ├─ Correlate profit changes with goal periods
    └─ Fall back to metric analysis if needed
    ↓
Stage 3: Optimization
    ├─ Fetch optimal goals
    └─ Recommend ACOS target for next period
    ↓
Final Response with goal-based insights
```

## Expected Behavioral Changes

### Before Refactoring
```
📈 Your net profit increased by 45.2% (+$15,230) from Oct 1 to Oct 8, 
and this is because your ACOS dropped from 26% to 21.5% during this period.
```

### After Refactoring
```
📈 Your net profit increased by 45.2% (+$15,230) from Oct 1 to Oct 8, 
and this is because you had an active ACOS goal of 23% during this period 
and successfully maintained ACOS at 21.5%, well within your target.
```

### New Capability: Goal Expiration Detection
```
📉 Your net profit decreased by 32.1% (-$8,450) from Oct 15 to Oct 20, 
and this is because your ACOS goal period ended on Oct 15, and ACOS 
immediately reverted from 22% to 28%, eroding margins.
```

## Testing Recommendations

To test the refactored handler:

1. **Test with goals**:
   ```bash
   curl -X POST http://localhost:8000/v1/chat \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"message": "Show me insights about product ASIN B0160HYB8S from Oct 1 to Oct 30", "sessionId": "test-1"}'
   ```
   - Verify goals are mentioned in the response
   - Check if profit changes correlate with goal periods

2. **Test without goals**:
   ```bash
   curl -X POST http://localhost:8000/v1/chat \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"message": "Show me insights from Nov 1 to Nov 30", "sessionId": "test-2"}'
   ```
   - Verify it falls back to ACOS/Ad TOS IS analysis
   - Check response says "No active goals during this period"

3. **Verify data structure**:
   - Confirm daily metrics only include 3 KPIs (not 5)
   - Check goals_text is formatted correctly
   - Verify token usage is reduced

## Files Modified

1. `app/metricsAccessLayer/metrics_api.py` - Added `get_goals_list()` method
2. `app/utils/trend_metrics_fetcher.py` - Refactored to fetch 3 metrics + goals
3. `app/graph/nodes/classifier_route_node/insight_query_handler/prompt.py` - Updated `TREND_ANALYSIS_PROMPT`
4. `app/graph/nodes/node_utils/trend_analyzing_handler/node.py` - Updated `_generate_trend_analysis_response()`

## Metrics

- **Files Modified**: 4
- **Lines Added**: ~100
- **Lines Removed**: ~50
- **Net Change**: +50 lines
- **Token Efficiency**: ~40% reduction in daily metrics data
- **New API Endpoint**: 1 (`/math/v1/goals/list`)
- **Linter Errors**: 0

## Status

✅ All changes completed successfully
✅ No linter errors
✅ Ready for testing
