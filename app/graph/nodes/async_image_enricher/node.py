"""
Async Image Enricher Node

Reusable node that enriches responses with product images and other metadata.
This node fetches product details (including image_link) for ASIN-based queries.

Can be attached after any handler that needs image enrichment.
"""

import logging
from app.models.agentState import AgentState

logger = logging.getLogger(__name__)


async def async_image_enricher_node(state: AgentState) -> AgentState:
    """
    Enriches response with product image URL for ASIN queries.
    
    This node:
    - Checks if ASIN exists in state
    - Fetches product details from Amazon backend API
    - Extracts image_link and updates state
    - Handles errors gracefully (image is optional enhancement)
    
    Can be reused across multiple query types that need image enrichment.
    """
    
    # Only fetch image if ASIN is present
    if not state.get('asin'):
        logger.debug("No ASIN in state, skipping image enrichment")
        return state
    
    asin = state['asin']
    logger.info(f"Enriching response with image for ASIN: {asin}")
    
    try:
        from app.metricsAccessLayer.products_api import products_api
        product_details = await products_api.get_product_details(asin)
        
        image_url = product_details.get('image_link')
        if image_url:
            state["image_url"] = image_url
            logger.info(f"Successfully fetched image URL for ASIN {asin}")
        else:
            logger.warning(f"No image_link in product details for ASIN {asin}")
            state["image_url"] = None
            
    except Exception as e:
        logger.warning(f"Failed to fetch image for ASIN {asin}: {e}")
        state["image_url"] = None
    
    return state

