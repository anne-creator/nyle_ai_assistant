"""
Inventory Tools - LangChain tools for COO inventory analysis.

Tools for:
1. get_current_doi - Current DOI Available and DOI Total
2. get_doi_trend - DOI trends over a period
3. get_storage_fees_summary - Storage fees summary
4. get_storage_fees_trend - Storage fees trends with all metrics
5. get_low_stock_asins - ASINs with low stock levels
"""

import asyncio
import json
import logging
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool

from app.metricsAccessLayer import metrics_api

logger = logging.getLogger(__name__)


# ==================== Input Schemas ====================

class DOIInput(BaseModel):
    """Input schema for DOI queries."""
    date_start: str = Field(description="Start date in YYYY-MM-DD format")
    date_end: str = Field(description="End date in YYYY-MM-DD format")
    asin: Optional[str] = Field(default=None, description="Optional ASIN filter")


class StorageFeesInput(BaseModel):
    """Input schema for storage fees queries."""
    date_start: str = Field(description="Start date in YYYY-MM-DD format")
    date_end: str = Field(description="End date in YYYY-MM-DD format")
    asin: Optional[str] = Field(default=None, description="Optional ASIN filter")


class LowStockInput(BaseModel):
    """Input schema for low stock queries."""
    date_start: str = Field(description="Start date in YYYY-MM-DD format (typically today)")
    threshold_days: int = Field(default=30, description="DOI threshold in days (default: 30)")


# ==================== Helper Functions ====================

def _safe_divide(numerator: float, denominator: float) -> float:
    """Safely divide two numbers, returning 0 if denominator is 0."""
    if denominator == 0 or denominator is None:
        return 0.0
    return numerator / denominator


def _extract_inventory_data(response: dict) -> dict:
    """Extract inventory metrics from API response."""
    if not isinstance(response, dict):
        logger.warning(f"Invalid response type: {type(response)}")
        return {}
    
    # Handle direct format (no timespan): {"daily_metrics": [...], "total_metrics": {...}}
    if "total_metrics" in response:
        total_metrics = response["total_metrics"]
        logger.info(f"Direct format - total_metrics: {total_metrics}")
        return total_metrics
    
    # Handle {"data": [...]} format (with timespan=day)
    if "data" in response and isinstance(response["data"], list):
        if len(response["data"]) > 0:
            data_item = response["data"][0]
            value = data_item.get("value", {})
            
            # Check if data is nested in total_metrics or daily_metrics
            if isinstance(value, dict):
                if "total_metrics" in value:
                    total_metrics = value["total_metrics"]
                    logger.info(f"Wrapped format - total_metrics: {total_metrics}")
                    return total_metrics
                elif "daily_metrics" in value:
                    return value["daily_metrics"]
            
            return value
    
    # Handle direct data format
    result = response.get("value", response)
    
    # Check for nested structure in direct format
    if isinstance(result, dict) and "total_metrics" in result:
        return result["total_metrics"]
    
    return result


def _extract_units_sold(response: dict) -> float:
    """Extract daily units sold from API response."""
    if not isinstance(response, dict):
        logger.warning(f"Invalid units sold response type: {type(response)}")
        return 0.0
    
    # Handle {"data": [...]} format
    if "data" in response and isinstance(response["data"], list):
        if len(response["data"]) > 0:
            data_item = response["data"][0]
            value = data_item.get("value", 0) or 0
            logger.info(f"Extracted units sold: {value}")
            return value
    
    # Handle direct value format
    value = response.get("value", 0) or 0
    return value


def _calculate_doi(inventory_data: dict, units_sold: float) -> tuple[float, float]:
    """
    Calculate DOI Available and DOI Total.
    
    Returns:
        (doi_available, doi_total)
    """
    available_stock = inventory_data.get("available_stock", 0) or 0
    in_transit = inventory_data.get("in_transit", 0) or 0
    receiving = inventory_data.get("receiving", 0) or 0
    
    doi_available = _safe_divide(available_stock, units_sold)
    doi_total = _safe_divide(available_stock + in_transit + receiving, units_sold)
    
    logger.info(f"DOI calculated - Available: {doi_available:.0f} days (stock: {available_stock}), Total: {doi_total:.0f} days (units/day: {units_sold:.0f})")
    
    return doi_available, doi_total


def _format_stockout_date(base_date: date, doi_available: float) -> str:
    """Calculate and format estimated stockout date."""
    days_to_add = int(doi_available)
    stockout_date = base_date + timedelta(days=days_to_add)
    return stockout_date.strftime("%b %d, %Y")


# ==================== Tool 1: Get Current DOI ====================

@tool(args_schema=DOIInput, return_direct=False)
async def get_current_doi(date_start: str, date_end: str, asin: Optional[str] = None) -> str:
    """
    Get current DOI (Days of Inventory) for today or a specific date.
    
    Returns DOI Available and DOI Total with formatted text.
    
    Args:
        date_start: Start date (YYYY-MM-DD)
        date_end: End date (YYYY-MM-DD)
        asin: Optional ASIN filter
    
    Returns:
        JSON string with DOI Available and DOI Total
    """
    logger.info(f"get_current_doi called: {date_start} to {date_end}, asin={asin}")
    
    try:
        # Fetch inventory metrics (without timespan to get raw data) and units sold in parallel
        inventory_response, units_response = await asyncio.gather(
            metrics_api.get_inventory_metrics(date_start, date_end, asin=asin),
            metrics_api.get_total_units_sold(date_start, date_end, asin=asin, timespan="day"),
            return_exceptions=True
        )
        
        # Handle errors
        if isinstance(inventory_response, Exception):
            logger.error(f"Inventory API error: {inventory_response}")
            return json.dumps({"status": "error", "message": "Failed to fetch inventory data"})
        
        if isinstance(units_response, Exception):
            logger.error(f"Units sold API error: {units_response}")
            return json.dumps({"status": "error", "message": "Failed to fetch units sold data"})
        
        # Extract data
        inventory_data = _extract_inventory_data(inventory_response)
        units_sold = _extract_units_sold(units_response)
        
        # Calculate DOI
        doi_available, doi_total = _calculate_doi(inventory_data, units_sold)
        
        # Format response
        result = {
            "status": "success",
            "doi_available": round(doi_available, 0),
            "doi_total": round(doi_total, 0),
            "units_sold_per_day": round(units_sold, 2),
            "text": f"DOI Available: {doi_available:.0f} days\nDOI Total: {doi_total:.0f} days"
        }
        
        logger.info(f"DOI calculated: Available={doi_available:.0f}, Total={doi_total:.0f}")
        return json.dumps(result)
    
    except Exception as e:
        logger.error(f"Error in get_current_doi: {e}", exc_info=True)
        return json.dumps({"status": "error", "message": str(e)})


# ==================== Tool 2: Get DOI Trend ====================

def _extract_daily_inventory_data(response: dict) -> list:
    """Extract daily inventory metrics from API response."""
    if not isinstance(response, dict):
        return []
    
    # Handle direct format: {"daily_metrics": [...], "total_metrics": {...}}
    if "daily_metrics" in response:
        logger.info(f"Found {len(response['daily_metrics'])} daily inventory records")
        return response["daily_metrics"]
    
    # Handle {"data": [...]} format (with timespan=day)
    if "data" in response and isinstance(response["data"], list):
        # Each item might have value with daily_metrics
        if len(response["data"]) > 0:
            first_item = response["data"][0]
            value = first_item.get("value", {})
            if isinstance(value, dict) and "daily_metrics" in value:
                return value["daily_metrics"]
        # Otherwise return the data list directly
        return response["data"]
    
    return []


@tool(args_schema=DOIInput, return_direct=False)
async def get_doi_trend(date_start: str, date_end: str, asin: Optional[str] = None) -> str:
    """
    Get DOI trends over a time period (e.g., last 30 days).
    
    Returns daily DOI values as markdown table.
    
    Args:
        date_start: Start date (YYYY-MM-DD)
        date_end: End date (YYYY-MM-DD)
        asin: Optional ASIN filter
    
    Returns:
        JSON string with daily DOI data and markdown table
    """
    logger.info(f"get_doi_trend called: {date_start} to {date_end}, asin={asin}")
    
    try:
        # Fetch inventory metrics (without timespan) and units sold (with timespan=day) in parallel
        inventory_response, units_response = await asyncio.gather(
            metrics_api.get_inventory_metrics(date_start, date_end, asin=asin),
            metrics_api.get_total_units_sold(date_start, date_end, asin=asin, timespan="day"),
            return_exceptions=True
        )
        
        # Handle errors
        if isinstance(inventory_response, Exception) or isinstance(units_response, Exception):
            logger.error(f"API error: inv={inventory_response}, units={units_response}")
            return json.dumps({"status": "error", "message": "Failed to fetch trend data"})
        
        # Extract daily inventory data (from direct format)
        inventory_list = _extract_daily_inventory_data(inventory_response)
        
        # Extract units sold data
        units_list = units_response.get("data", []) if isinstance(units_response, dict) else []
        
        logger.info(f"Got {len(inventory_list)} inventory days, {len(units_list)} units days")
        
        # Build daily DOI records
        daily_data = []
        max_len = max(len(inventory_list), len(units_list))
        
        for i in range(max_len):
            if i < len(inventory_list) and i < len(units_list):
                inv_item = inventory_list[i]
                units_item = units_list[i]
                
                # inventory_list items are direct: {"date": "...", "available_stock": ...}
                # units_list items are wrapped: {"period_start": "...", "value": ...}
                units_value = units_item.get("value", 0) or 0
                
                doi_available, doi_total = _calculate_doi(inv_item, units_value)
                
                daily_data.append({
                    "date": inv_item.get("date", "")[:10],
                    "doi_available": round(doi_available, 0),
                    "doi_total": round(doi_total, 0)
                })
        
        # Build markdown table
        table_lines = ["| Date | DOI Available | DOI Total |"]
        table_lines.append("|------|---------------|-----------|")
        
        for day in daily_data:
            table_lines.append(f"| {day['date']} | {day['doi_available']:.0f} days | {day['doi_total']:.0f} days |")
        
        markdown_table = "\n".join(table_lines)
        
        result = {
            "status": "success",
            "daily_data": daily_data,
            "markdown_table": markdown_table,
            "text": f"Here's your DOI trend from {date_start} to {date_end}:\n\n{markdown_table}"
        }
        
        logger.info(f"DOI trend calculated: {len(daily_data)} days")
        return json.dumps(result)
    
    except Exception as e:
        logger.error(f"Error in get_doi_trend: {e}", exc_info=True)
        return json.dumps({"status": "error", "message": str(e)})


# ==================== Tool 3: Get Storage Fees Summary ====================

@tool(args_schema=StorageFeesInput, return_direct=False)
async def get_storage_fees_summary(date_start: str, date_end: str, asin: Optional[str] = None) -> str:
    """
    Get storage fees summary for a period.
    
    Returns storage costs, FBA in-stock rate, and inventory turnover.
    Handles null values gracefully.
    
    Args:
        date_start: Start date (YYYY-MM-DD)
        date_end: End date (YYYY-MM-DD)
        asin: Optional ASIN filter
    
    Returns:
        JSON string with storage metrics
    """
    logger.info(f"get_storage_fees_summary called: {date_start} to {date_end}, asin={asin}")
    
    try:
        # Fetch executive summary
        response = await metrics_api.get_inventory_status(date_start, date_end, asin=asin, timespan="day")
        
        if isinstance(response, Exception):
            return json.dumps({"status": "error", "message": "Failed to fetch storage fees data"})
        
        # Extract data
        data = _extract_inventory_data(response)
        
        storage_costs = data.get("storage_costs")
        fba_in_stock_rate = data.get("fba_in_stock_rate")
        inventory_turnover = data.get("inventory_turnover")
        
        # Build text response with null handling
        text_lines = []
        
        if storage_costs is not None:
            text_lines.append(f"Storage Fees: ${storage_costs:,.2f}")
        else:
            text_lines.append("Storage Fees: Data not available yet")
        
        if fba_in_stock_rate is not None:
            text_lines.append(f"FBA In-Stock Rate: {fba_in_stock_rate:.1f}%")
        
        if inventory_turnover is not None and inventory_turnover > 0:
            text_lines.append(f"Inventory Turnover: {inventory_turnover:.1f}x per year")
        
        result = {
            "status": "success",
            "storage_costs": storage_costs,
            "fba_in_stock_rate": fba_in_stock_rate,
            "inventory_turnover": inventory_turnover,
            "text": "\n".join(text_lines)
        }
        
        logger.info(f"Storage fees summary: {storage_costs}")
        return json.dumps(result)
    
    except Exception as e:
        logger.error(f"Error in get_storage_fees_summary: {e}", exc_info=True)
        return json.dumps({"status": "error", "message": str(e)})


# ==================== Tool 4: Get Storage Fees Trend ====================

@tool(args_schema=StorageFeesInput, return_direct=False)
async def get_storage_fees_trend(date_start: str, date_end: str, asin: Optional[str] = None) -> str:
    """
    Get storage fees trends with all related metrics over a period.
    
    Returns time series for: storage fees, DOI, ROI, FBA in-stock rate, inventory turnover.
    Handles partial data gracefully.
    
    Args:
        date_start: Start date (YYYY-MM-DD)
        date_end: End date (YYYY-MM-DD)
        asin: Optional ASIN filter
    
    Returns:
        JSON string with multi-metric time series data
    """
    logger.info(f"get_storage_fees_trend called: {date_start} to {date_end}, asin={asin}")
    
    try:
        # Fetch all metrics in parallel
        inventory_response, units_response, executive_response, roi_response = await asyncio.gather(
            metrics_api.get_inventory_metrics(date_start, date_end, asin=asin),
            metrics_api.get_total_units_sold(date_start, date_end, asin=asin, timespan="day"),
            metrics_api.get_inventory_status(date_start, date_end, asin=asin, timespan="day"),
            metrics_api.get_daily_roi(date_start, date_end, asin=asin, timespan="day"),
            return_exceptions=True
        )
        
        # Extract daily inventory data (direct format)
        inventory_list = _extract_daily_inventory_data(inventory_response) if isinstance(inventory_response, dict) else []
        units_list = units_response.get("data", []) if isinstance(units_response, dict) else []
        executive_list = executive_response.get("data", []) if isinstance(executive_response, dict) else []
        roi_list = roi_response.get("data", []) if isinstance(roi_response, dict) else []
        
        # Build daily multi-metric records
        daily_data = []
        max_len = max(len(inventory_list), len(units_list), len(executive_list), len(roi_list))
        
        for i in range(max_len):
            record = {}
            
            # Get date from inventory (direct format has "date" field)
            if i < len(inventory_list):
                record["date"] = inventory_list[i].get("date", "")[:10]
            elif i < len(units_list):
                record["date"] = units_list[i].get("period_start", "")[:10]
            elif i < len(roi_list):
                record["date"] = roi_list[i].get("period_start", "")[:10]
            else:
                continue
            
            # Calculate DOI (always available)
            if i < len(inventory_list) and i < len(units_list):
                inv_item = inventory_list[i]  # Direct format: {"date": "...", "available_stock": ...}
                units_value = units_list[i].get("value", 0) or 0
                doi_available, doi_total = _calculate_doi(inv_item, units_value)
                record["doi_available"] = round(doi_available, 0)
                record["doi_total"] = round(doi_total, 0)
            
            # ROI (always available)
            if i < len(roi_list):
                record["roi"] = round(roi_list[i].get("value", 0) or 0, 2)
            
            # Storage fees (may be null)
            if i < len(executive_list):
                exec_value = executive_list[i].get("value", {})
                record["storage_costs"] = exec_value.get("storage_costs")
                record["fba_in_stock_rate"] = exec_value.get("fba_in_stock_rate")
                record["inventory_turnover"] = exec_value.get("inventory_turnover")
            
            daily_data.append(record)
        
        # Build markdown table with available metrics
        has_storage = any(d.get("storage_costs") is not None for d in daily_data)
        has_fba_rate = any(d.get("fba_in_stock_rate") is not None for d in daily_data)
        has_turnover = any(d.get("inventory_turnover") is not None for d in daily_data)
        
        # Build table headers
        headers = ["Date", "DOI Available", "DOI Total", "ROI"]
        if has_storage:
            headers.append("Storage Fees")
        if has_fba_rate:
            headers.append("FBA In-Stock Rate")
        if has_turnover:
            headers.append("Inventory Turnover")
        
        table_lines = ["| " + " | ".join(headers) + " |"]
        table_lines.append("|" + "|".join(["------"] * len(headers)) + "|")
        
        # Build table rows
        for day in daily_data:
            row = [
                day.get("date", ""),
                f"{day.get('doi_available', 0):.0f} days",
                f"{day.get('doi_total', 0):.0f} days",
                f"{day.get('roi', 0):.1f}%"
            ]
            if has_storage:
                storage = day.get("storage_costs")
                row.append(f"${storage:,.2f}" if storage is not None else "N/A")
            if has_fba_rate:
                fba = day.get("fba_in_stock_rate")
                row.append(f"{fba:.1f}%" if fba is not None else "N/A")
            if has_turnover:
                turnover = day.get("inventory_turnover")
                row.append(f"{turnover:.1f}x" if turnover is not None else "N/A")
            
            table_lines.append("| " + " | ".join(row) + " |")
        
        markdown_table = "\n".join(table_lines)
        
        # Build text with notes about missing data
        text = f"Here's your storage fees trend from {date_start} to {date_end}:\n\n{markdown_table}"
        if not has_storage:
            text += "\n\n**Note:** Storage Fees data not available yet"
        
        result = {
            "status": "success",
            "daily_data": daily_data,
            "markdown_table": markdown_table,
            "has_storage_costs": has_storage,
            "has_fba_in_stock_rate": has_fba_rate,
            "has_inventory_turnover": has_turnover,
            "text": text
        }
        
        logger.info(f"Storage fees trend calculated: {len(daily_data)} days")
        return json.dumps(result)
    
    except Exception as e:
        logger.error(f"Error in get_storage_fees_trend: {e}", exc_info=True)
        return json.dumps({"status": "error", "message": str(e)})


# ==================== Tool 5: Get Low Stock ASINs ====================

@tool(args_schema=LowStockInput, return_direct=False)
async def get_low_stock_asins(date_start: str, threshold_days: int = 30) -> str:
    """
    Find ASINs with low stock levels (DOI below threshold).
    
    Returns markdown table with ASINs, DOI, and estimated stockout dates.
    
    Args:
        date_start: Start date (YYYY-MM-DD, typically today)
        threshold_days: DOI threshold in days (default: 30)
    
    Returns:
        JSON string with low stock ASINs data and recommendations
    """
    logger.info(f"get_low_stock_asins called: date={date_start}, threshold={threshold_days}")
    
    try:
        # Use same date for start and end (single day query)
        date_end = date_start
        
        # Fetch inventory metrics, units sold, and executive summary (without ASIN filter to get all)
        inventory_response, units_response, executive_response = await asyncio.gather(
            metrics_api.get_inventory_metrics(date_start, date_end),
            metrics_api.get_total_units_sold(date_start, date_end, timespan="day"),
            metrics_api.get_inventory_status(date_start, date_end, timespan="day"),
            return_exceptions=True
        )
        
        # Handle errors
        if isinstance(inventory_response, Exception) or isinstance(units_response, Exception):
            return json.dumps({"status": "error", "message": "Failed to fetch inventory data"})
        
        # Extract data - use total_metrics from inventory response
        inventory_data = _extract_inventory_data(inventory_response) if isinstance(inventory_response, dict) else {}
        units_list = units_response.get("data", []) if isinstance(units_response, dict) else []
        
        # Get units sold (first day's value)
        units_sold = 0
        if len(units_list) > 0:
            units_sold = units_list[0].get("value", 0) or 0
        
        # Build ASIN-level data
        low_stock_asins = []
        base_date = datetime.strptime(date_start, "%Y-%m-%d").date()
        
        # Calculate DOI from total_metrics
        doi_available, doi_total = _calculate_doi(inventory_data, units_sold)
        
        # Get safety stock
        safety_stock = inventory_data.get("safety_stock", 0) or 0
        
        # Check if below threshold
        if doi_available < threshold_days:
            # Calculate stockout date
            stockout_date = _format_stockout_date(base_date, doi_available)
            
            low_stock_asins.append({
                "asin": "All Products",  # Without ASIN filter, this is account-level
                "doi_available": round(doi_available, 0),
                "doi_total": round(doi_total, 0),
                "stockout_date": stockout_date,
                "safety_stock": safety_stock
            })
        
        if not low_stock_asins:
            return json.dumps({
                "status": "success",
                "low_stock_asins": [],
                "text": f"Great news! No ASINs found with DOI below {threshold_days} days."
            })
        
        # Build markdown table
        table_lines = ["| ASIN | DOI Available | DOI Total | Estimated Stock-Out Date |"]
        table_lines.append("|------|---------------|-----------|--------------------------|")
        
        for asin_data in low_stock_asins:
            table_lines.append(
                f"| {asin_data['asin']} | {asin_data['doi_available']:.0f} days | "
                f"{asin_data['doi_total']:.0f} days | {asin_data['stockout_date']} |"
            )
        
        markdown_table = "\n".join(table_lines)
        
        # Build recommendation based on safety stock
        avg_safety_stock = sum(a["safety_stock"] for a in low_stock_asins) / len(low_stock_asins)
        
        if avg_safety_stock == 0:
            recommendation = (
                "**Recommendation:**\n"
                "Probability of Out of Stock. Safety stock is currently 0 days. "
                "It is necessary to promptly replenish stock according to ASINs."
            )
        elif avg_safety_stock < 15:
            recommendation = (
                f"**Recommendation:**\n"
                f"Probability of Out of Stock. Safety stock is only {avg_safety_stock:.0f} days. "
                f"It is necessary to promptly replenish stock according to ASINs."
            )
        else:
            recommendation = (
                f"**Recommendation:**\n"
                f"Moderate stock levels detected. Safety stock is {avg_safety_stock:.0f} days. "
                f"Monitor these ASINs closely."
            )
        
        text = (
            f"ASINs with less than {threshold_days} days of stock:\n\n"
            f"{markdown_table}\n\n{recommendation}"
        )
        
        result = {
            "status": "success",
            "low_stock_asins": low_stock_asins,
            "markdown_table": markdown_table,
            "recommendation": recommendation,
            "text": text
        }
        
        logger.info(f"Found {len(low_stock_asins)} ASINs with low stock")
        return json.dumps(result)
    
    except Exception as e:
        logger.error(f"Error in get_low_stock_asins: {e}", exc_info=True)
        return json.dumps({"status": "error", "message": str(e)})
