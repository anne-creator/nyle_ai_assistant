# Hardcoded questions that have pre-defined responses
HARDCODED_QUESTIONS = {
    "show me performance insights",
    "give me performance insights",
    "what was the highest performance day?",
    "what day had the best performance?",
    "can you compare my store performance in august over august to september?",
    "can you show me some insights about this product from oct 1 to oct 30",
    "yes",
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
    "insight",
    "trend",
    "trends",
    "trending",
    "analyze",
    "analysis",
    "what happened",
    "dropped",
    "decreased",
    "increased",
]

# Keywords that indicate inventory/COO queries
INVENTORY_KEYWORDS = [
    "doi",
    "days of inventory",
    "day of inventory",
    "storage fee",
    "storage fees",
    "storage cost",
    "inventory",
    "stock",
    "stockout",
    "stock out",
    "safety stock",
    "available stock",
    "in transit",
    "receiving",
    "low stock",
    "out of stock",
    "inventory turnover",
    "fba in-stock",
    "fba in stock",
]

# AI prompt for distinguishing metrics_query vs other_query
METRICS_VS_OTHER_PROMPT = """Classify this question into ONE category:

**Categories:**

1. **metrics_query** - Questions asking for business data, metrics, or performance numbers from the user's Amazon seller account
Examples:
- "What's my ACOS?"
- "What is ACOS?"
- "What is ROI?"
- "What is my ROI?"
- "Show me total sales"
- "Give me an overview of store performance"
- "How are my sales doing today?"
- "What's the conversion rate?"

2. **other_query** - General questions, greetings, or EXPLICIT requests for concept definitions/explanations (must use words like "mean", "explain", "define")
Examples:
- "Hi"
- "How are you?"
- "Who are you?"
- "What can you do for me?"
- "What does ACOS mean?"
- "What does ROI mean?"
- "Explain ACOS to me"
- "Define conversion rate"
- "What is the meaning of ACOS?"
- "How does Amazon FBA work?"

**Critical Rules:**
1. "What is [anything]?" → DEFAULT to metrics_query unless the question explicitly asks for meaning/definition/explanation
2. ONLY classify as other_query if the user explicitly uses words like: "mean", "means", "meaning", "explain", "define", "definition"
3. When uncertain between metrics_query and other_query, ALWAYS choose metrics_query

**Question:** {question}

**Return ONLY the category name (no explanation).**"""
