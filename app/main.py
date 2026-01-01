from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional
import logging

from app.config import get_settings
from app.context import RequestContext
from app.graph.builder import create_chatbot_graph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Nyle Chatbot", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load settings first to set LangSmith environment variables
settings = get_settings()
logger.info(f"LangSmith tracing enabled: {settings.langchain_tracing_v2}")
logger.info(f"LangSmith project: {settings.langchain_project}")

# Create graph instance (after settings are loaded)
graph = create_chatbot_graph()

# Security scheme for Swagger UI
security = HTTPBearer()


def get_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract JWT token from Bearer credentials."""
    return credentials.credentials


# http call schema
class ChatRequest(BaseModel):
    # Core message fields
    message: str = Field(..., description="User's question or message", example="What are my total sales?")
    sessionId: str = Field(..., description="Unique session identifier for conversation history", example="abc123")
    
    # Interaction type
    interaction_type: Optional[str] = Field(None, description="Type of interaction. Use 'dashboard_load' when user opens dashboard page.", example="dashboard_load")

    # Optional date overrides
    date_start: Optional[str] = Field(None, description="Optional start date override (ISO format)", example="2025-12-01")
    date_end: Optional[str] = Field(None, description="Optional end date override (ISO format)", example="2025-12-31")
    type: Optional[str] = Field(None, description="Query type hint (legacy field)")
    ASIN: Optional[str] = Field(None, description="Optional ASIN override", example="B08XYZ1234")
    timespan: Optional[str] = Field(None, description="Optional timespan hint")
    compare_start_date: Optional[str] = Field(None, description="Optional comparison period start date", example="2025-11-01")
    compare_end_date: Optional[str] = Field(None, description="Optional comparison period end date", example="2025-11-30")


class ChatResponse(BaseModel):
    message: str = Field(..., description="Response text (supports markdown)", example="Your ACOS is 24.32%")
    image_url: Optional[str] = Field(None, description="Product image URL. Only present for ASIN queries. Frontend should handle load failures.", example="https://m.media-amazon.com/images/I/71zzJgMMKwL.jpg")
    asin: Optional[str] = Field(None, description="Product ASIN code. Present when query is about specific product.", example="B08XYZ1234")
    date_range: Optional[dict] = Field(None, description="Time period covered by this response", example={"start_date": "2025-12-16", "end_date": "2025-12-22", "label": "Last 7 days"})


@app.post("/chatbot", response_model=ChatResponse, responses={
    200: {
        "description": "Successful response",
        "content": {
            "application/json": {
                "examples": {
                    "simple_query": {
                        "summary": "Simple metrics query",
                        "value": {
                            "message": "Your total sales for the last 7 days is $45,320.",
                            "image_url": None,
                            "asin": None,
                            "date_range": {
                                "start_date": "2025-12-16",
                                "end_date": "2025-12-22",
                                "label": "Last 7 days"
                            }
                        }
                    },
                    "dashboard_load": {
                        "summary": "Dashboard load event",
                        "value": {
                            "message": "Your products dashboard is ready! Ask me anything about your products.",
                            "image_url": None,
                            "asin": None,
                            "date_range": None
                        }
                    },
                    "asin_query": {
                        "summary": "ASIN query with product image",
                        "value": {
                            "message": "**Product B08XYZ1234 Performance**\n\nSales: $45,320\nUnits: 1,234\nROI: 32.5%",
                            "image_url": "https://m.media-amazon.com/images/I/71zzJgMMKwL.jpg",
                            "asin": "B08XYZ1234",
                            "date_range": {
                                "start_date": "2025-12-16",
                                "end_date": "2025-12-22",
                                "label": "Last 7 days"
                            }
                        }
                    }
                }
            }
        }
    }
})
async def chatbot(
    request: ChatRequest,
    jwt_token: str = Depends(get_jwt_token)
):
    """
    Main chatbot endpoint for Amazon seller analytics.
    
    ## Usage Scenarios
    
    ### 1. Normal Queries
    Send natural language questions about your products:
    - "What are my total sales?"
    - "Show me top 5 products"
    - "Analyze product B08XYZ1234"
    
    ### 2. Dashboard Load
    When user opens the dashboard page, notify the chatbot:
    - Set `message` to empty string or placeholder
    - Set `interaction_type` to "dashboard_load"
    - Chatbot responds with greeting (no AI processing needed)
    
    ### 3. Product Image Rendering
    When response includes `image_url`:
    - Check if field exists and is not None
    - Render image with error handling
    - Always render message text (image is optional enhancement)
    
    Image URLs are from Amazon CDN. If image fails to load, gracefully hide it.
    
    ## Response Fields
    - `message`: Always present, contains response text (supports markdown)
    - `image_url`: Optional, only for ASIN queries
    - `asin`: Optional, only when query is about specific product
    - `date_range`: Optional, time period covered by the response
    """
    
    logger.info(f"Received question: {request.message}")
    
    # Set up request context using async context manager
    async with RequestContext(jwt_token=jwt_token, session_id=request.sessionId):
        # Build initial state - maps HTTP request to AgentState
        initial_state = {
            "_jwt_token": jwt_token,  # Store JWT in state for reliable access
            "messages": [("human", request.message)],
            "question": request.message,
            "interaction_type": request.interaction_type,  # NEW: Pass through interaction type
            "_http_date_start": request.date_start,
            "_http_date_end": request.date_end,
            "_http_compare_date_start": request.compare_start_date,
            "_http_compare_date_end": request.compare_end_date,
            "_http_asin": request.ASIN,
            "_date_start_label": None,
            "_date_end_label": None,
            "_compare_date_start_label": None,
            "_compare_date_end_label": None,
            "_explicit_date_start": None,
            "_explicit_date_end": None,
            "_explicit_compare_start": None,
            "_explicit_compare_end": None,
            "_custom_days_count": None,
            "_custom_compare_days_count": None,
            "date_start": None,
            "date_end": None,
            "compare_date_start": None,
            "compare_date_end": None,
            "asin": None,
            "_normalizer_valid": None,
            "_normalizer_retries": None,
            "_normalizer_feedback": None,
            "question_type": "",
            "requested_metrics": None,
            "metric_data": None,
            "comparison_metric_data": None,
            "image_url": None,  # NEW: Initialize image_url
            "response": ""
        }
        
        # Run graph
        config = {
            "configurable": {
                "thread_id": request.sessionId,
                "jwt_token": jwt_token  # Pass JWT through config for reliable access
            }
        }
        result = await graph.ainvoke(initial_state, config)
        
        logger.info(f"Generated response")
        
        # Extract response data from state
        message = result.get("response", "")
        image_url = result.get("image_url")
        asin = result.get("asin")
        
        # Construct date_range if dates are present
        date_range = None
        if result.get("date_start") and result.get("date_end"):
            date_range = {
                "start_date": result["date_start"],
                "end_date": result["date_end"],
                "label": None  # Could be enhanced to include label like "Last 7 days"
            }
        
        return ChatResponse(
            message=message,
            image_url=image_url,
            asin=asin,
            date_range=date_range
        )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

