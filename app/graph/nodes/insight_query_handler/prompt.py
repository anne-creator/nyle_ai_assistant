# Sub-classification prompt for insight intents
INSIGHT_INTENT_PROMPT = """Classify this question into ONE insight type:

**Types:**

1. **net_profit_loss** - Questions about net profit losses, non-optimal ad spend, wasted money
Examples:
- "What was my net profit losses over Oct 15 - Oct 30?"
- "How much did I lose on ads?"
- "What's my non-optimal spend?"

2. **comparison** - General comparison between two periods
Examples:
- "Compare August vs September"
- "How did sales change from Q1 to Q2?"
- "Week over week performance"

**Question:** {question}

**Return ONLY the type name (no explanation).**"""


# LLM explanation prompt for net profit loss
NET_PROFIT_LOSS_EXPLANATION_PROMPT = """Generate a clear explanation for the user's net profit loss data.

**Data:**
- Period A ({period_a_start} to {period_a_end}): Non-optimal spend = ${non_optimal_a:,.2f}
- Period B ({period_b_start} to {period_b_end}): Non-optimal spend = ${non_optimal_b:,.2f}
- Delta: ${delta:,.2f}
- TACoS Period A: {tacos_a}%
- TACoS Period B: {tacos_b}%

**User Question:** {question}

**Instructions:**
- Start with the net profit loss amount for the requested period
- Explain the change compared to the previous period
- Reference TACoS changes as a contributing factor
- Keep it concise (2-3 sentences)
- Use $ for currency with commas
- Use % for percentages

**Response:**"""


# LLM explanation prompt for general comparison
COMPARISON_EXPLANATION_PROMPT = """You are an Amazon seller analytics assistant specialized in period comparisons.

## Your Role
Compare metrics between two time periods and highlight changes.

## Response Format
Always show:
- **Period 1 (earlier):** [formatted value]
- **Period 2 (recent):** [formatted value]
- **Change:** [absolute change] ([percentage change])

Example:
**August 2025:** $1,750,000
**September 2025:** $1,935,035
**Change:** +$185,035 (+10.6% increase)

## Formatting Rules
- Currency: Add $ and commas
- Percentage: Show with % sign
- Changes: Use + for increases, - for decreases
- Always include both period labels"""

