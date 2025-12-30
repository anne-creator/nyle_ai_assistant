"""
Response Templates for ASIN Product Handler.

Templates are stored separately for maintainability and injection into prompts.
"""

# For ranking queries (top/bottom N) - includes Total Sales, Net Profit, ROI
# Format: ASIN: B08XYZ1234 - Total Sales: $xxx | Net Profit: $xxx | ROI: xx%
RANKING_ITEM_TEMPLATE = """ASIN: {asin} - Total Sales: ${total_sales:,.0f} | Net Profit: ${net_profit:,.0f} | ROI: {roi:.0f}%"""

# For single ASIN queries - same format as ranking but for one product
# Format: For your specific ASIN: B08XYZ123 Total Sales yesterday (Dec 17): $2,400 | Units: 150
SINGLE_ASIN_TEMPLATE = """For your specific ASIN: {asin} Total Sales ({date_range}): ${total_sales:,.0f} | Units: {units:,}"""

# Available order_by fields for ranking (from executive_summary)
RANKABLE_FIELDS = [
    "total_sales",
    "net_profit",
    "gross_profit",
    "gross_margin",
    "contribution_margin",
    "roi",
]

# Template selector mapping
TEMPLATES = {
    "ranking_item": RANKING_ITEM_TEMPLATE,
    "single_asin": SINGLE_ASIN_TEMPLATE,
}


def format_templates_for_prompt() -> str:
    """Format templates for injection into system prompt."""
    return f"""
## Response Templates

### Ranking Query Response (per item):
{RANKING_ITEM_TEMPLATE}

**IMPORTANT: Add an empty line between each ASIN entry.**

Example output for "top 5 selling ASINs":
ASIN: B08XYZ1234 - Total Sales: $2,400 | Net Profit: $1,200 | ROI: 50%

ASIN: B09ABC4567 - Total Sales: $1,800 | Net Profit: $900 | ROI: 45%

ASIN: B07DEF7891 - Total Sales: $950 | Net Profit: $475 | ROI: 40%

### Single ASIN Query Response:
{SINGLE_ASIN_TEMPLATE}

Example output for "How many units of B08XYZ123 did I sell yesterday":
For your specific ASIN: B08XYZ123 Total Sales (Dec 17): $2,400 | Units: 150
"""

