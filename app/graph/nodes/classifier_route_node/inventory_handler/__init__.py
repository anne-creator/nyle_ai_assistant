"""
Inventory Handler - COO inventory management and DOI analysis.

Handles questions about:
- Days of Inventory (DOI)
- Storage fees and costs
- Stockout risks and low stock alerts
"""

from .node import inventory_handler_node

__all__ = ["inventory_handler_node"]
