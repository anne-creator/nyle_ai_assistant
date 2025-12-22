CLASSIFIER_PROMPT = """Classify this Amazon seller question into ONE category:

**Categories:**

1. **metrics_query** - Questions about store-level metrics
   Examples:
   - "What is my ACOS?"
   - "Show me total sales for last month"
   - "What was my net profit yesterday?"
   - "Give me my store overview"

2. **compare_query** - Questions comparing TWO time periods
   Examples:
   - "Compare August vs September"
   - "How did sales change from last month to this month?"
   - "Show Q1 compared to Q2"
   - "What's the difference between last week and this week?"

3. **asin_product** - Questions about a SPECIFIC product (ASIN)
   Examples:
   - "What are sales for ASIN B0B5HN65QQ?"
   - "Show me performance of product B0DP55J8ZG"
   - "How is ASIN B0D3VHMR3Z doing?"
   - "When will B0B5HN65QQ go out of stock?"

4. **hardcoded** - Special questions with pre-defined responses
   Examples:
   - "Show me performance insights"
   - "What was the highest performance day?"

**Question:** {question}

**Return ONLY the category name (no explanation).**"""

