import logging
from pydantic import BaseModel, Field
from typing import Optional
from langchain_openai import ChatOpenAI

from app.models.agentState import AgentState
from app.config import get_settings
from app.graph.nodes.extractor_evaluator.prompt import EXTRACTOR_EVALUATOR_PROMPT

logger = logging.getLogger(__name__)


class EvaluationResult(BaseModel):
    """
    Structured output from the extractor evaluator AI agent.
    
    This model captures only the AI's assessment - retry counting
    is handled in the node logic itself.
    """
    is_valid: bool = Field(
        description="True if extraction is correct, False if issues found"
    )
    feedback: Optional[str] = Field(
        default=None,
        description="Specific, actionable feedback if invalid. None if valid."
    )


def extractor_evaluator_node(state: AgentState) -> AgentState:
    """
    THIRD NODE: AI-powered evaluator that validates Node 1 and Node 2 outputs.
    
    Features:
    - Validates label extraction accuracy (Node 1)
    - Validates date calculation correctness (Node 2)
    - Provides feedback for regeneration
    - Manages retry counter (max 3 attempts)
    - Forces continuation after max retries to prevent infinite loops
    
    Inputs (from previous nodes):
        - question: user's question
        - Node 1 outputs: labels, metadata, ASIN
        - Node 2 outputs: calculated dates
        - _normalizer_retries: current retry count
    
    Outputs (updates state):
        - _normalizer_valid: bool (whether extraction passed)
        - _normalizer_retries: int (incremented if invalid)
        - _normalizer_feedback: str (guidance for correction)
    """
    
    logger.info("🔍 Extractor Evaluator: Starting validation")
    
    # Get current retry count (initialize to 0 if not present or None)
    current_retries = state.get("_normalizer_retries")
    if current_retries is None:
        current_retries = 0
    logger.info(f"📊 Current retry attempt: {current_retries + 1} of 3")
    
    # Check if we've exceeded max retries
    if current_retries >= 3:
        logger.error("❌ Max retries (3) exceeded - forcing continuation with error")
        state["_normalizer_valid"] = True  # Force valid to break loop
        state["_normalizer_retries"] = current_retries
        state["_normalizer_feedback"] = "Max retries exceeded - proceeding with current extraction"
        return state
    
    # Prepare data for evaluation
    question = state.get("question", "")
    
    # Node 1 outputs
    date_start_label = state.get("_date_start_label")
    date_end_label = state.get("_date_end_label")
    compare_start_label = state.get("_compare_date_start_label")
    compare_end_label = state.get("_compare_date_end_label")
    custom_days = state.get("_custom_days_count")
    custom_compare_days = state.get("_custom_compare_days_count")
    explicit_start = state.get("_explicit_date_start")
    explicit_end = state.get("_explicit_date_end")
    explicit_compare_start = state.get("_explicit_compare_start")
    explicit_compare_end = state.get("_explicit_compare_end")
    asin = state.get("asin")
    
    # Node 2 outputs
    date_start = state.get("date_start")
    date_end = state.get("date_end")
    compare_date_start = state.get("compare_date_start")
    compare_date_end = state.get("compare_date_end")
    
    # Create evaluation prompt
    prompt = EXTRACTOR_EVALUATOR_PROMPT.format(
        question=question,
        date_start_label=date_start_label or "None",
        date_end_label=date_end_label or "None",
        compare_date_start_label=compare_start_label or "None",
        compare_date_end_label=compare_end_label or "None",
        custom_days_count=custom_days or "None",
        custom_compare_days_count=custom_compare_days or "None",
        explicit_date_start=explicit_start or "None",
        explicit_date_end=explicit_end or "None",
        explicit_compare_start=explicit_compare_start or "None",
        explicit_compare_end=explicit_compare_end or "None",
        asin=asin or "None",
        date_start=date_start or "None",
        date_end=date_end or "None",
        compare_date_start=compare_date_start or "None",
        compare_date_end=compare_date_end or "None",
        retry_count=current_retries
    )
    
    try:
        # Initialize LLM with structured output
        settings = get_settings()
        llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0,
            api_key=settings.openai_api_key
        )
        llm_with_structure = llm.with_structured_output(EvaluationResult)
        
        # Get evaluation from AI
        evaluation: EvaluationResult = llm_with_structure.invoke(prompt)
        
        # Update state based on evaluation
        state["_normalizer_valid"] = evaluation.is_valid
        state["_normalizer_feedback"] = evaluation.feedback
        
        # Increment retry count ONLY if invalid
        if not evaluation.is_valid:
            state["_normalizer_retries"] = current_retries + 1
            logger.warning(f"⚠️ Validation failed: {evaluation.feedback}")
            logger.info(f"🔄 Will retry (attempt {current_retries + 2} of 3)")
        else:
            # Keep retry count as is (don't reset - track total attempts)
            state["_normalizer_retries"] = current_retries
            logger.info("✅ Validation passed - extraction is correct")
        
    except Exception as e:
        logger.error(f"❌ Error during evaluation: {e}")
        # On error, mark as valid to continue pipeline (fail-safe)
        state["_normalizer_valid"] = True
        state["_normalizer_retries"] = current_retries
        state["_normalizer_feedback"] = f"Evaluation error: {str(e)}"
    
    return state

