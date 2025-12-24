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

## Evaluations

### 3-Node Subgraph Evaluation

Evaluate the first 3 nodes of the pipeline together: `label_normalizer → message_analyzer → extractor_evaluator`

**Location:** `evaluations/subgraph_eval/`

#### Files Structure

```
evaluations/subgraph_eval/
├── config.py          # Configuration (dataset name, experiment prefix)
├── dataset.csv        # 46 test examples (23 without ASIN + 23 with ASIN)
├── evaluators.py      # All evaluator functions
├── wrappers.py        # Subgraph builder + state conversion
└── run_eval.py        # Main runner script
```

#### Evaluator Standards

**Node 1 (label_normalizer) - 7 Evaluators:**

| Evaluator | Criteria | Score |
|-----------|----------|-------|
| `node1_date_start_label` | Exact match of date_start_label | 1.0 or 0.0 |
| `node1_date_end_label` | Exact match of date_end_label | 1.0 or 0.0 |
| `node1_asin` | Exact match (empty string = no ASIN) | 1.0 or 0.0 |
| `node1_compare_labels` | Both compare_start and compare_end labels match | 1.0 or 0.0 |
| `node1_custom_days` | custom_days_count matches (for "past 17 days" etc.) | 1.0 or 0.0 |
| `node1_explicit_dates` | Explicit start/end dates match (YYYY-MM-DD) | 1.0 or 0.0 |
| `node1_explicit_compare_dates` | Explicit comparison dates match | 1.0 or 0.0 |

**Node 2 (message_analyzer) - Pass-through node:**
- Currently does nothing (pass-through mode)

**Node 3 (extractor_evaluator) - Pass-through node:**
- Currently does nothing (pass-through mode)

**Pass-Through (metadata capture) - 3 Evaluators:**

| Evaluator | Criteria | Score |
|-----------|----------|-------|
| `normalizer_valid_passthrough` | Captures `_normalizer_valid` value | Always 1.0 |
| `normalizer_retries_passthrough` | Captures `_normalizer_retries` value | Always 1.0 |
| `normalizer_feedback_passthrough` | Captures `_normalizer_feedback` value | Always 1.0 |

**Combined - 1 Evaluator:**

| Evaluator | Criteria | Score |
|-----------|----------|-------|
| `pipeline_accuracy` | ALL Node 1 evaluators pass | 1.0 only if all pass |

#### How to Run

1. **Upload dataset to LangSmith:**
   - Go to https://smith.langchain.com
   - Create dataset named: `nyle-subgraph-dataset`
   - Upload: `evaluations/subgraph_eval/dataset.csv`
   - Set **Inputs**: `question`, `current_date`, `http_asin`, `http_date_start`, `http_date_end`, `sessionid`
   - Set **Outputs**: all `node1_*` columns (date labels, ASIN, validation metadata)

2. **Run evaluation:**
   ```bash
   python evaluations/subgraph_eval/run_eval.py
   ```

3. **View results:**
   - Go to https://smith.langchain.com
   - Navigate to **Experiments** tab
   - Find experiment: `subgraph-eval-*`
   - Inspect per-node outputs and evaluator scores

#### Dataset Examples

The dataset includes 46 examples covering:
- **Relative dates:** today, yesterday, this week, last week
- **Year periods:** this year, last year, YTD
- **Months:** December, June, etc.
- **Quarters:** Q3 (last quarter)
- **Past X days:** past 7 days, past 90 days, custom (past 17 days)
- **Explicit dates:** "Oct 1 to Dec 3", "Dec 1 to Oct 15"
- **Comparisons:** "today vs yesterday", "this week vs last week", "Sep to Dec"
- **With ASIN:** All above examples repeated with `B08XYZ1234`

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
START
  ↓
┌─────────────────────────────────┐
│   label_normalizer             │  ← FIRST NODE (Active)
│                                 │
│ - Extracts date labels         │
│ - Extracts ASIN                 │
│ - Self-evaluates extraction     │
│ - Retries up to 3 times if     │
│   extraction not valid          │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│   message_analyzer              │  ← PASS-THROUGH (does nothing)
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│   extractor_evaluator           │  ← PASS-THROUGH (does nothing)
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│   classifier                    │  ← Classifies question type
│                                 │
│ - metrics_query                 │
│ - compare_query                 │
│ - asin_product                  │
│ - hardcoded                     │
│                                 │
│ + Re-classifies if ASIN found   │
└────────────┬────────────────────┘
             ↓
        Route by type
             ↓
    ┌────────┴────────┬──────────────┬──────────────┐
    ↓                 ↓              ↓              ↓
metrics_query    compare_query  asin_product   hardcoded
  handler          handler        handler      response
    ↓                 ↓              ↓              ↓
    └─────────────────┴──────────────┴──────────────┘
                      ↓
                     END
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
        ├── label_normalizer/      # Extracts date labels and ASIN (with retry)
        ├── message_analyzer/      # Pass-through node
        ├── extractor_evaluator/   # Pass-through node
        ├── classifier/            # Classifies question type
        ├── metrics_query_handler/
        ├── compare_query_handler/
        ├── asin_product_handler/
        └── hardcoded_response/
```

