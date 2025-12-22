from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import logging

from app.config import get_settings
from app.context import RequestContext
from app.graph.builder import create_chatbot_graph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Nyle Chatbot", version="1.0.0")

# Load settings first to set LangSmith environment variables
settings = get_settings()
logger.info(f"LangSmith tracing enabled: {settings.langchain_tracing_v2}")
logger.info(f"LangSmith project: {settings.langchain_project}")

# Create graph instance (after settings are loaded)
graph = create_chatbot_graph()


class ChatRequest(BaseModel):
    message: str
    sessionId: str
    date_start: Optional[str] = None
    date_end: Optional[str] = None


class ChatResponse(BaseModel):
    myField: str


@app.post("/chatbot", response_model=ChatResponse)
async def chatbot(
    request: ChatRequest,
    authorization: str = Header(None)
):
    """Main chatbot endpoint."""
    
    # Validate JWT
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    jwt_token = authorization.replace("Bearer ", "")
    
    logger.info(f"Received question: {request.message}")
    
    # Set up request context
    with RequestContext(jwt_token=jwt_token, session_id=request.sessionId):
        # Build initial state
        initial_state = {
            "messages": [],
            "question": request.message,
            "date_start": request.date_start or "",
            "date_end": request.date_end or "",
            "compare_date_start": None,
            "compare_date_end": None,
            "asin": None,
            "question_type": "",
            "requested_metrics": None,
            "metric_data": None,
            "comparison_metric_data": None,
            "response": ""
        }
        
        # Run graph
        config = {"configurable": {"thread_id": request.sessionId}}
        result = await graph.ainvoke(initial_state, config)
        
        logger.info(f"Generated response")
        
        return ChatResponse(myField=result.get("response", ""))


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

