from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
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
    # Existing fields (backward compatible)
    message: str
    sessionId: str

    date_start: Optional[str] = None
    date_end: Optional[str] = None
    type: Optional[str] = None
    ASIN: Optional[str] = None
    timespan: Optional[str] = None
    compare_start_date: Optional[str] = None
    compare_end_date: Optional[str] = None


class ChatResponse(BaseModel):
    myField: str


@app.post("/chatbot", response_model=ChatResponse)
async def chatbot(
    request: ChatRequest,
    jwt_token: str = Depends(get_jwt_token)
):
    """Main chatbot endpoint."""
    
    logger.info(f"Received question: {request.message}")
    
    # Set up request context
    with RequestContext(jwt_token=jwt_token, session_id=request.sessionId):
        # Build initial state - maps HTTP request to AgentState
        initial_state = {
            "messages": [("human", request.message)],
            "question": request.message,
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

