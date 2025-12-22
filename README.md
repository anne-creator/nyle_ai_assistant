# Nyle Chatbot

Amazon seller analytics chatbot built with LangGraph and FastAPI.

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create `.env.local`, `.env.dev`, or `.env.production` based on your environment:

```bash
# kill port if in use
kill -9 $(lsof -ti:8000)

# Environment: local | dev | production
ENVIRONMENT=local

# OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini

# API Base URLs
DEV_API_BASE_URL=https://api0.dev.nyle.ai/math/v1
PROD_API_BASE_URL=https://api.nyle.ai/math/v1

# LangSmith (optional)
LANGCHAIN_TRACING_V2=false
LANGCHAIN_PROJECT=nyle-chatbot
LANGCHAIN_API_KEY=your-langsmith-api-key
```

### 3. Run the Server

```bash
# Local development
ENVIRONMENT=local uvicorn app.main:app --reload --port 8000

# Dev environment (Vercel)
ENVIRONMENT=dev uvicorn app.main:app --port 8000

# Production (Vercel)
ENVIRONMENT=production uvicorn app.main:app --port 8000
```

## Debug

### Enable Logging

Logs are printed to stdout. Set log level in your environment:

```bash
LOG_LEVEL=DEBUG uvicorn app.main:app --reload
```

### Test Single Request

```bash
curl -X POST http://localhost:8000/chatbot \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzY2Mjg4MDEzLCJpYXQiOjE3NjYyODc3MTMsImp0aSI6ImIwNGY4ZGY4MjgxNDRiMjdiMDAzODRiYTlkYWFhYTE5Iiwic3ViIjoiNGY4OWJlOWUtZTljMS00M2YyLWI1NzMtNTVjNmNlZTM0NDQxIiwiaXNzIjoibnlsZS5haSJ9.zUAZCPyK8btQ6KY4sJndwoDzuUUG_VtlhRfdbx6Y2eI" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my ACOS?", "sessionId": "test-123"}'
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_nodes.py -v
```

## Data Structures

### AgentState

State object passed through the LangGraph execution:

```python
{
    "messages": [],           # Conversation history
    "question": str,          # User's question
    "date_start": str,        # Start date (YYYY-MM-DD)
    "date_end": str,          # End date (YYYY-MM-DD)
    "compare_date_start": str, # Comparison start (for compare_query)
    "compare_date_end": str,   # Comparison end (for compare_query)
    "asin": str,              # Product ASIN (for asin_product)
    "question_type": str,     # metrics_query | compare_query | asin_product | hardcoded
    "response": str           # Final response
}
```

### API Request/Response

**Request:**
```json
{
    "message": "What is my ACOS?",
    "sessionId": "user-123",
    "date_start": "2025-09-01",  // optional
    "date_end": "2025-09-14"     // optional
}
```

**Response:**
```json
{
    "myField": "Your ACOS is **25.5%** (Sep 1-14, 2025)"
}
```

## Main Features

### 4 Question Types

1. **metrics_query** - Store-level metrics (ACOS, sales, profit)
2. **compare_query** - Period comparisons (August vs September)
3. **asin_product** - Product-specific queries (placeholder)
4. **hardcoded** - Pre-defined responses

### Graph Flow

```
START → Classifier → Date Extraction → Handler → END
                         ↓
              (metrics/comparison/asin)
```

## LangSmith

### Enable Tracing

Set these environment variables:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=nyle-chatbot-dev
LANGCHAIN_API_KEY=your-langsmith-api-key
```

### View Traces

1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Select your project (e.g., `nyle-chatbot-dev`)
3. View traces for each request

### What LangSmith Shows

- Full LLM prompts and responses
- Tool calls and results
- Node execution order
- Latency per node
- Token usage and costs

## Project Structure

```
app/
├── main.py              # FastAPI entry point
├── config.py            # Environment settings
├── context.py           # Request context (JWT)
├── models/state.py      # AgentState definition
├── api/                 # API access layer
│   ├── client.py        # Base HTTP client
│   ├── metrics.py       # Metrics endpoints
│   └── comparison.py    # Comparison endpoints
└── graph/
    ├── builder.py       # LangGraph construction
    └── nodes/           # Node implementations
        ├── classifier/
        ├── extract_dates_metrics/
        ├── extract_dates_comparison/
        ├── extract_dates_asin/
        ├── metrics_query_handler/
        ├── compare_query_handler/
        ├── asin_product_handler/
        └── hardcoded_response/
```

