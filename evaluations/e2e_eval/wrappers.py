"""
Wrapper functions for end-to-end graph evaluation.

Creates evaluation target that runs the complete graph without HTTP calls.
"""
from typing import Dict, Any
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.models.agentState import AgentState
from app.graph.graph import create_graph


def create_e2e_target():
    """
    Create end-to-end evaluation target.
    
    Returns a function that:
    1. Takes LangSmith input (question, current_date, etc.)
    2. Runs the complete graph
    3. Returns structured output for evaluation
    """
    
    async def e2e_target(inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run complete graph end-to-end.
        
        Args:
            inputs: Dict with keys:
                - question: User's question
                - current_date: Current date (YYYY-MM-DD)
                - http_asin: ASIN from HTTP request (optional)
                - http_date_start: Date start from HTTP (optional)
                - http_date_end: Date end from HTTP (optional)
                - sessionid: Session ID
        
        Returns:
            Dict with evaluation outputs:
                - response: Final response text
                - final_answer: Final answer from graph
                - nodes_executed: List of nodes that were executed
                - error: Error message if any
        """
        try:
            # Build initial state
            initial_state = AgentState(
                question=inputs.get("question", ""),
                current_date=inputs.get("current_date", ""),
                http_asin=inputs.get("http_asin", ""),
                http_date_start=inputs.get("http_date_start", ""),
                http_date_end=inputs.get("http_date_end", ""),
                sessionid=inputs.get("sessionid", ""),
                messages=[]
            )
            
            # Create and run graph
            graph = create_graph()
            final_state = await graph.ainvoke(initial_state)
            
            # Extract outputs
            return {
                "response": final_state.get("final_answer", ""),
                "final_answer": final_state.get("final_answer"),
                "nodes_executed": final_state.get("_nodes_executed", []),
                "error": None
            }
            
        except Exception as e:
            return {
                "response": "",
                "final_answer": None,
                "nodes_executed": [],
                "error": str(e)
            }
    
    return e2e_target

