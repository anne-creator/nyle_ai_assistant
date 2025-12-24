from langchain_openai import ChatOpenAI
import logging

from app.models.agentState import AgentState
from app.config import get_settings
from app.graph.nodes.label_normalizer.prompt import LABEL_NORMALIZER_PROMPT

logger = logging.getLogger(__name__)


def label_normalizer_node(state: AgentState) -> AgentState:
    """
    Normalize labels in the question or extracted data.
    """
    
    logger.info("Normalizing labels")
    
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key
    )
    
    prompt = LABEL_NORMALIZER_PROMPT.format(question=state["question"])
    
    response = llm.invoke(prompt)
    normalized_content = response.content.strip()
    
    # Update state with normalized content
    state["normalized_labels"] = normalized_content
    logger.info(f"Normalized labels: {normalized_content}")
    
    return state

