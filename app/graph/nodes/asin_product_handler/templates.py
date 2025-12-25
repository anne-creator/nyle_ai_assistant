"""
Response Templates for ASIN Product Handler.

Templates are stored separately for maintainability and injection into prompts.
"""

# For single ASIN queries with specific product
SINGLE_ASIN_TEMPLATE = """For ASIN: {asin}
Total Sales ({date_range}): **${total_sales:,.0f}**"""
# Future: Add | Units: {units:,} | CVR: {cvr:.1f}% when service available

# For ranking queries (top/bottom N) - uses fields from /amazon/v1/products/own
RANKING_ITEM_TEMPLATE = """ASIN: {asin} - Total Sales: **${total_sales:,.0f}** | Net Profit: **${net_profit:,.0f}** | ROI: **{roi:.1f}%**"""
# Future: Add Units/CVR when service available

# For simple metric queries
SIMPLE_METRIC_TEMPLATE = """Your {metric_name} is **{formatted_value}** ({date_range}) for ASIN: {asin}"""

# Available order_by fields for ranking (from executive_summary)
RANKABLE_FIELDS = [
    "executive_summary.total_sales",
    "executive_summary.net_profit",
    "executive_summary.gross_profit",
    "executive_summary.gross_margin",
    "executive_summary.contribution_margin",
    "executive_summary.roi",
]

# Template selector mapping
TEMPLATES = {
    "single_asin": SINGLE_ASIN_TEMPLATE,
    "ranking_item": RANKING_ITEM_TEMPLATE,
    "simple_metric": SIMPLE_METRIC_TEMPLATE,
}


def format_templates_for_prompt() -> str:
    """Format templates for injection into system prompt."""
    return f"""
## Response Templates

### Single ASIN Response:
{SINGLE_ASIN_TEMPLATE}

### Ranking Query Response (per item):
{RANKING_ITEM_TEMPLATE}

### Simple Metric Response:
{SIMPLE_METRIC_TEMPLATE}
"""

