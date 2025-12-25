import logging
from langchain_openai import ChatOpenAI

from app.models.agentState import AgentState
from app.config import get_settings

logger = logging.getLogger(__name__)


def other_handler_node(state: AgentState) -> AgentState:
    """
    Handler for questions that don't fit into other categories.
    
    Handles:
    - General questions
    - Unclassifiable queries
    - Fallback responses
    """
    
    logger.info(f"Processing other/unclassified query: '{state['question']}'")
    
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.7,
        api_key=settings.openai_api_key
    )
    
    # Generate a helpful response for unclassified questions
    prompt = f"""You are a helpful assistant for an Amazon seller. The user has asked a question that doesn't fit into our standard categories (metrics, comparisons, product-specific, or hardcoded responses).

Question: {state['question']}

Provide a helpful, professional response. If the question is unclear, ask for clarification. If it's outside your scope, politely explain what types of questions you can help with (metrics queries, comparisons, product information, etc.).

Keep your response concise and friendly."""
    
    response = llm.invoke(prompt)
    state["response"] = response.content.strip()
    
    logger.info("Returned other/fallback response")
    
    return state

