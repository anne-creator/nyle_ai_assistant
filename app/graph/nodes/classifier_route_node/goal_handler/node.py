import logging
from langchain_openai import ChatOpenAI

from app.models.agentState import AgentState
from app.config import get_settings
from .prompt import (
    GOAL_HANDLER_PROMPT,
    GOAL_CREATED_CONFIRMATION,
    GOAL_CREATION_FAILED_MESSAGE
)

logger = logging.getLogger(__name__)


def goal_handler_node(state: AgentState) -> AgentState:
    """
    Handler for goal-related queries and goal creation events.
    
    Handles:
    1. interaction_type "goal_created" - Returns success confirmation message
    2. interaction_type "goal_created_failed" - Returns failure message
    3. Goal-related questions - Uses AI to provide goal management responses
    """
    
    question = state.get("question", "")
    interaction_type = state.get("interaction_type", "")
    
    logger.info(f"Processing goal query: '{question}' with interaction_type: '{interaction_type}'")
    
    # Handle goal_created interaction type
    if interaction_type == "goal_created":
        logger.info("Detected goal_created interaction type")
        state["response"] = GOAL_CREATED_CONFIRMATION
        return state
    
    # Handle goal_created_failed interaction type
    if interaction_type == "goal_created_failed":
        logger.info("Detected goal_created_failed interaction type")
        state["response"] = GOAL_CREATION_FAILED_MESSAGE
        return state
    
    # Handle actual goal-related questions
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.7,
        api_key=settings.openai_api_key,
        streaming=True
    )
    
    # Generate goal management response
    prompt = GOAL_HANDLER_PROMPT.format(question=question)
    response = llm.invoke(prompt)
    
    state["response"] = response.content.strip()
    logger.info("Generated goal management response")
    
    return state
