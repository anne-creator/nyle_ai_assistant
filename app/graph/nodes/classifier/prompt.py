# Hardcoded questions that have pre-defined responses
HARDCODED_QUESTIONS = {
    "show me performance insights",
    "give me performance insights",
    "what was the highest performance day?",
    "what day had the best performance?",
    "can you compare my store performance in august over august to september?",
}

# Keywords that indicate insight/comparison queries
INSIGHT_KEYWORDS = [
    "compare",
    "compared",
    "comparison",
    "versus",
    "vs",
    "difference",
    "differences",
    "variance",
    "change",
    "shift",
    "shifted",
    "week over week",
    "month over month",
    "year over year",
    "loss",
    "losses",
    "why",
    "insights",
    "dropped",
    "decreased",
]

# AI prompt for distinguishing metrics_query vs other_query
METRICS_VS_OTHER_PROMPT = """Classify this question into ONE category:

**Categories:**

1. **metrics_query** - Questions asking for business data, metrics, or performance numbers from the user's Amazon seller account
Examples:
- "What's my ACOS?"
- "Show me total sales"
- "What is my ROI?"
- "Give me an overview of store performance"
- "How are my sales doing today?"

2. **other_query** - General questions, greetings, definitions, or questions not related to business metrics
Examples:
- "Hi"
- "How are you?"
- "Who are you?"
- "What can you do for me?"
- "What is ACOS?" (asking for definition, not data)
- "How does Amazon FBA work?"

**Question:** {question}

**Return ONLY the category name (no explanation).**"""
