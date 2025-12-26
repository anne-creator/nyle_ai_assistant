import logging
import random
from langchain_openai import ChatOpenAI

from app.models.agentState import AgentState
from app.config import get_settings
from .prompt import (
    SUB_CLASSIFY_PROMPT,
    GREETING_RESPONSES,
    ABOUT_SERVICE_RESPONSE,
    KNOWLEDGE_ANSWER_PROMPT
)

logger = logging.getLogger(__name__)


def other_handler_node(state: AgentState) -> AgentState:
    """
    Handler for questions classified as 'other_query'.

    Handles three types:
    1. Greetings - Simple welcome messages
    2. About service - What Nyle/chatbot does
    3. Knowledge questions - eCommerce terminology definitions
    """

    logger.info(f"Processing other query: '{state['question']}'")

    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0.3,
        api_key=settings.openai_api_key
    )

    # Sub-classify the query type
    classify_prompt = SUB_CLASSIFY_PROMPT.format(question=state['question'])
    classification = llm.invoke(classify_prompt)
    query_type = classification.content.strip().lower()

    logger.info(f"Sub-classified as: {query_type}")

    # Route based on sub-type
    if query_type == "greeting":
        state["response"] = random.choice(GREETING_RESPONSES)
        logger.info("Returned greeting response")

    elif query_type == "about_service":
        state["response"] = ABOUT_SERVICE_RESPONSE
        logger.info("Returned about service response")

    elif query_type == "knowledge":
        # Use web search for knowledge questions
        knowledge_prompt = KNOWLEDGE_ANSWER_PROMPT.format(question=state['question'])
        response = llm.invoke(knowledge_prompt)
        state["response"] = response.content.strip()
        logger.info("Returned knowledge response")

    else:
        # Fallback for unrecognized sub-types
        state["response"] = random.choice(GREETING_RESPONSES)
        logger.warning(f"Unrecognized sub-type '{query_type}', using greeting fallback")

    return state


