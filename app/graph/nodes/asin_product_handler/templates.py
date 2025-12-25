"""
Response Templates for ASIN Product Handler.

Templates are stored separately for maintainability and injection into prompts.
"""

# For ranking queries (top/bottom N) - includes Total Sales, Units, CVR
# Format: ASIN: B08XYZ1234 - Total Sales: $2,400 | Units: 150 | CVR: 8%
RANKING_ITEM_TEMPLATE = """ASIN: {asin} - Total Sales: ${total_sales:,.0f} | Units: {units:,} | CVR: {cvr:.0f}%"""

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

Example output for "top 5 selling ASINs":
ASIN: B08XYZ1234 - Total Sales: $2,400 | Units: 150 | CVR: 8%
ASIN: B09ABC4567 - Total Sales: $1,800 | Units: 90 | CVR: 6%
ASIN: B07DEF7891 - Total Sales: $950 | Units: 200 | CVR: 12%

### Single ASIN Query Response:
{SINGLE_ASIN_TEMPLATE}

Example output for "How many units of B08XYZ123 did I sell yesterday":
For your specific ASIN: B08XYZ123 Total Sales (Dec 17): $2,400 | Units: 150
"""

