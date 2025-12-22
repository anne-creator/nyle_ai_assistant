"""
Simple Metrics Tool - AI Agent for retrieving specific metrics from multiple APIs.

This tool is an AI agent that:
1. Receives a list of metric names
2. Determines which API endpoints to call
3. Retrieves data from those endpoints
4. Returns only the requested metrics in a structured format
"""

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import logging
import json

from app.config import get_settings
from app.graph.nodes.metrics_query_handler.simple_metrics_tool.prompt import SIMPLE_METRICS_SYSTEM_PROMPT
from app.metricsAccessLayer import metrics_api

logger = logging.getLogger(__name__)

# Store context for tool access
_current_context = {}


class MetricsInput(BaseModel):
    """Input schema for the simple metrics tool."""
    metric_list: List[str] = Field(description="List of metric names to retrieve (e.g., ['acos', 'total_sales', 'net_profit'])")
    date_start: str = Field(description="Start date in YYYY-MM-DD format")
    date_end: str = Field(description="End date in YYYY-MM-DD format")


class MetricsOutput(BaseModel):
    """Output schema for the simple metrics tool."""
    metrics: Dict[str, Any] = Field(description="Dictionary of requested metrics with their values")
    status: str = Field(description="Status of the operation (success/error)")
    message: str = Field(default="", description="Optional message about the operation")


@tool(args_schema=MetricsInput, return_direct=False)
async def get_simple_metrics(metric_list: List[str], date_start: str, date_end: str) -> str:
    """
    Retrieve specific metrics from Nyle backend APIs.
    
    This tool intelligently determines which API endpoints to call based on the requested metrics,
    fetches the data, and returns only the requested metrics in a structured JSON format.
    
    Args:
        metric_list: List of metric names to retrieve (e.g., ['acos', 'total_sales', 'net_profit'])
        date_start: Start date in YYYY-MM-DD format
        date_end: End date in YYYY-MM-DD format
        
    Returns:
        JSON string containing only the requested metrics with their values
    """
    global _current_context
    _current_context = {
        "metric_list": metric_list,
        "date_start": date_start,
        "date_end": date_end
    }
    
    logger.info(f"Simple Metrics Tool called with metrics: {metric_list}, dates: {date_start} to {date_end}")
    
    settings = get_settings()
    
    # Define the 6 API tools
    @tool
    async def GET_ads_executive_summary() -> dict:
        """
        Fetch advertising metrics from Nyle backend.
        
        Returns: ad_sales, ad_spend, ad_clicks, ad_impressions, ad_units_sold, ad_orders, 
                 acos, roas, cpc, cac, ad_ctr, ad_cvr, time_in_budget
        """
        logger.info("Calling GET_ads_executive_summary")
        result = await metrics_api.get_ads_executive_summary(
            _current_context["date_start"],
            _current_context["date_end"]
        )
        logger.info("Retrieved ads executive summary")
        return result
    
    @tool
    async def GET_total_executive_summary() -> dict:
        """
        Fetch total/overall metrics from Nyle backend.
        
        Returns: total_sales, total_units_sold, total_spend, total_clicks, total_orders, 
                 total_impressions, cvr, tacos, mer, net_proceeds, ctr, cogs, monthly_budget, 
                 lost_sales, roi, contribution_margin, contribution_profit, gross_margin
        """
        logger.info("Calling GET_total_executive_summary")
        result = await metrics_api.get_total_metrics_summary(
            _current_context["date_start"],
            _current_context["date_end"]
        )
        logger.info("Retrieved total executive summary")
        return result
    
    @tool
    async def GET_cfo_executive_summary() -> dict:
        """
        Fetch financial/CFO metrics from Nyle backend.
        
        Returns: available_capital, frozen_capital, borrowed_capital, lost_sales, 
                 cost_of_goods_sold, gross_profit, net_profit, amazon_fees, misc, 
                 contribution_profit, gross_margin, contribution_margin, net_margin, 
                 opex, ebitda, roi
        """
        logger.info("Calling GET_cfo_executive_summary")
        result = await metrics_api.get_financial_summary(
            _current_context["date_start"],
            _current_context["date_end"]
        )
        logger.info("Retrieved CFO executive summary")
        return result
    
    @tool
    async def GET_organic_executive_summary() -> dict:
        """
        Fetch organic performance metrics from Nyle backend.
        
        Returns: organic_impressions, organic_clicks, organic_orders, organic_units_sold, 
                 organic_cvr, organic_ctr, organic_sales, organic_lost_sales, 
                 organic_add_to_cart (+ all _what_if variants)
        """
        logger.info("Calling GET_organic_executive_summary")
        result = await metrics_api.get_organic_metrics(
            _current_context["date_start"],
            _current_context["date_end"]
        )
        logger.info("Retrieved organic executive summary")
        return result
    
    @tool
    async def GET_attribution_executive_summary() -> dict:
        """
        Fetch attribution metrics from Nyle backend.
        
        Returns: attribution_sales, attribution_spend, attribution_impressions, 
                 attribution_clicks, attribution_units_sold, attribution_orders, 
                 attribution_ctr, attribution_cvr, attribution_acos, attribution_roas, 
                 attribution_cpc, attribution_cpm, attribution_add_to_cart
        """
        logger.info("Calling GET_attribution_executive_summary")
        result = await metrics_api.get_attribution_metrics(
            _current_context["date_start"],
            _current_context["date_end"]
        )
        logger.info("Retrieved attribution executive summary")
        return result
    
    @tool
    async def GET_inventory_metrics_executive_summary() -> dict:
        """
        Fetch inventory metrics from Nyle backend.
        
        Returns: safety_stock, inventory_turnover, fba_in_stock_rate
        """
        logger.info("Calling GET_inventory_metrics_executive_summary")
        result = await metrics_api.get_inventory_status(
            _current_context["date_start"],
            _current_context["date_end"]
        )
        logger.info("Retrieved inventory metrics executive summary")
        return result
    
    # Create the LLM
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key
    )
    
    # Create the agent with all 6 tools
    agent = create_agent(
        llm,
        tools=[
            GET_ads_executive_summary,
            GET_total_executive_summary,
            GET_cfo_executive_summary,
            GET_organic_executive_summary,
            GET_attribution_executive_summary,
            GET_inventory_metrics_executive_summary
        ],
        system_prompt=SIMPLE_METRICS_SYSTEM_PROMPT
    )
    
    logger.info("Running simple metrics agent...")
    
    # Prepare the input message
    input_message = f"""metrics list: {json.dumps(metric_list)}
date_start: {date_start}
date_end: {date_end}"""
    
    try:
        # Invoke the agent asynchronously (required for async tools)
        result = await agent.ainvoke({
            "messages": [("human", input_message)]
        })
        
        # Extract the final response
        final_response = result["messages"][-1].content
        
        logger.info(f"Agent completed. Response: {final_response}")
        
        # Try to parse and validate the response as JSON
        try:
            # Clean up the response (remove markdown code blocks if present)
            cleaned_response = final_response.strip()
            if cleaned_response.startswith("```"):
                # Remove markdown code blocks
                lines = cleaned_response.split("\n")
                cleaned_response = "\n".join([l for l in lines if not l.startswith("```")])
            
            # Parse JSON to validate
            parsed_metrics = json.loads(cleaned_response)
            
            # Return structured response
            output = {
                "status": "success",
                "metrics": parsed_metrics,
                "message": f"Successfully retrieved {len(parsed_metrics)} metrics"
            }
            
            return json.dumps(output)
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse agent response as JSON: {e}")
            # Return the raw response wrapped in our structure
            output = {
                "status": "success",
                "metrics": {},
                "message": final_response
            }
            return json.dumps(output)
    
    except Exception as e:
        logger.error(f"Error in simple metrics agent: {str(e)}", exc_info=True)
        output = {
            "status": "error",
            "metrics": {},
            "message": f"Error retrieving metrics: {str(e)}"
        }
        return json.dumps(output)
