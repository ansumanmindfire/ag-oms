from typing import Dict, Any, Optional
from app.config import settings, logger


def process_query(prompt: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Execute the configured orchestration workflow.

    Args:
        prompt: Natural language customer request.
        session_id: Optional session ID for multi-turn tracking.

    Returns:
        Dict with 'session_id' and 'answer'.
    """
    mode = settings.ORCHESTRATION_MODE.lower().strip()
    logger.info(f"Orchestration mode: '{mode}'")

    if mode == "supervisor":
        from app.agents import supervisor_agent
        return supervisor_agent.run(prompt=prompt, session_id=session_id)

    from app.graph import run_oms_graph
    return run_oms_graph(prompt=prompt, session_id=session_id)
