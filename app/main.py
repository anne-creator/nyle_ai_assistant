from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, AsyncIterator
import logging
import json

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
    
    # Streaming option
    stream: Optional[bool] = Field(False, description="Enable streaming response (word-by-word). Returns SSE stream if true, JSON if false.", example=False)
    
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


@app.post("/chatbot", responses={
    200: {
        "description": "Successful response. Returns JSON by default, or SSE stream if stream=true",
        "content": {
            "application/json": {
                "examples": {
                    "simple_query": {
                        "summary": "Simple metrics query",
                        "value": {
                            "message": "Your total sales for the last 7 days is $45,320.",
                            "image_url": None,
                            "asin": None
                        }
                    },
                    "dashboard_load": {
                        "summary": "Dashboard load event",
                        "value": {
                            "message": "Your products dashboard is ready! Ask me anything about your products.",
                            "image_url": None,
                            "asin": None
                        }
                    },
                    "asin_query": {
                        "summary": "ASIN query with product image",
                        "value": {
                            "message": "**Product B08XYZ1234 Performance**\n\nSales: $45,320\nUnits: 1,234\nROI: 32.5%",
                            "image_url": "https://m.media-amazon.com/images/I/71zzJgMMKwL.jpg",
                            "asin": "B08XYZ1234"
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
    
    ## Streaming Mode
    Set `stream: true` in request body to enable word-by-word streaming.
    - Returns Server-Sent Events (SSE) instead of JSON
    - Frontend should use EventSource or fetch with streaming
    - Event types: 'token', 'metadata', 'done', 'error'
    
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
    - Chatbot routes through classifier to dashboard_load_handler
    - Currently returns hardcoded greeting template
    - Future: Will fetch live data (product count, recent sales, alerts, etc.)
    
    ### 3. Product Image Rendering
    When response includes `image_url`:
    - Check if field exists and is not None
    - Render image with error handling
    - Always render message text (image is optional enhancement)
    
    Image URLs are from Amazon CDN. If image fails to load, gracefully hide it.
    
    ## Response Fields (JSON mode)
    - `message`: Always present, contains response text (supports markdown)
    - `image_url`: Optional, only for ASIN queries
    - `asin`: Optional, only when query is about specific product
    """
    
    logger.info(f"Received question: {request.message} (stream={request.stream})")
    
    # Build initial state - maps HTTP request to AgentState
    initial_state = {
        "_jwt_token": jwt_token,
        "messages": [("human", request.message)],
        "question": request.message,
        "interaction_type": request.interaction_type,
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
        "question_type": "",
        "requested_metrics": None,
        "metric_data": None,
        "comparison_metric_data": None,
        "image_url": None,
        "response": ""
    }
    
    config = {
        "configurable": {
            "thread_id": request.sessionId,
            "jwt_token": jwt_token
        }
    }
    
    # Route based on streaming preference
    if request.stream:
        # Return streaming response
        async def event_generator() -> AsyncIterator[str]:
            """Generate SSE events from the graph stream."""
            try:
                async with RequestContext(jwt_token=jwt_token, session_id=request.sessionId):
                    final_image_url = None
                    final_asin = None
                    
                    # Stream events from the graph
                    async for event in graph.astream_events(initial_state, config, version="v2"):
                        kind = event.get("event")
                        
                        # Stream LLM tokens
                        if kind == "on_chat_model_stream":
                            chunk = event.get("data", {}).get("chunk")
                            if chunk and hasattr(chunk, "content") and chunk.content:
                                yield f"event: token\ndata: {json.dumps({'token': chunk.content})}\n\n"
                        
                        # Capture final state for metadata
                        elif kind == "on_chain_end":
                            output = event.get("data", {}).get("output", {})
                            if isinstance(output, dict):
                                if "image_url" in output and output["image_url"]:
                                    final_image_url = output["image_url"]
                                if "asin" in output and output["asin"]:
                                    final_asin = output["asin"]
                    
                    # Send final metadata
                    if final_image_url or final_asin:
                        yield f"event: metadata\ndata: {json.dumps({'image_url': final_image_url, 'asin': final_asin})}\n\n"
                    
                    # Send completion event
                    yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"
                    logger.info("Stream completed successfully")
            
            except Exception as e:
                logger.error(f"Stream error: {str(e)}", exc_info=True)
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    else:
        # Return JSON response (original behavior)
        async with RequestContext(jwt_token=jwt_token, session_id=request.sessionId):
            result = await graph.ainvoke(initial_state, config)
            
            logger.info(f"Generated response")
            
            # Extract response data from state
            message = result.get("response", "")
            image_url = result.get("image_url")
            asin = result.get("asin")
            
            return ChatResponse(
                message=message,
                image_url=image_url,
                asin=asin
            )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

