"""Orchestration Service coordinating multi-agent workflows (Supervisor vs LangGraph)."""

from typing import Dict, Any, Optional, Generator
from app.config import settings, logger


class OrchestrationService:
    """Service class for dispatching queries to the active orchestration backend."""

    @staticmethod
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

    @staticmethod
    def stream_query(prompt: str, session_id: Optional[str] = None) -> Generator[Dict[str, Any], None, None]:
        """Execute the configured orchestration workflow in streaming mode.

        Args:
            prompt: Natural language customer request.
            session_id: Optional session ID for multi-turn tracking.

        Yields:
            Dict events with 'type': 'session' | 'token'.
        """
        mode = settings.ORCHESTRATION_MODE.lower().strip()
        logger.info(f"Streaming orchestration mode: '{mode}'")

        if mode == "supervisor":
            from app.agents import supervisor_agent
            yield from supervisor_agent.stream(prompt=prompt, session_id=session_id)
            return

        from app.graph import stream_oms_graph
        yield from stream_oms_graph(prompt=prompt, session_id=session_id)

