from typing import Dict, Any, Optional, Generator
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk
from langchain.agents import create_agent

from app.config import logger
from app.constants import AGENT_TEMPERATURE
from app.llm import get_llm, extract_text_content
from app.tools.agent_tools import supervisor_tools
from app.prompts import SUPERVISOR_SYSTEM_PROMPT
from app.graph.checkpointer import checkpointer
from app.utils.session import resolve_session_id
from app.utils.streaming import get_tool_status_message



class SupervisorAgent:
    """Supervisor Agent that orchestrates domain agents autonomously via ReAct tool calling.

    Uses SqliteSaver checkpointer for automatic multi-turn session persistence,
    identical to how the LangGraph StateGraph approach handles memory.
    """

    def __init__(self):
        self._llm = get_llm(temperature=AGENT_TEMPERATURE)
        self.agent = create_agent(
            model=self._llm,
            tools=supervisor_tools,
            system_prompt=SUPERVISOR_SYSTEM_PROMPT,
            checkpointer=checkpointer,
        )

    def run(
        self,
        prompt: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute the Supervisor Agent pipeline.

        Args:
            prompt: Natural language customer request.
            session_id: Optional session ID for multi-turn tracking.

        Returns:
            Dict with 'session_id' and 'answer'.
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        active_session_id = resolve_session_id(session_id)
        logger.info(f"Running Supervisor Agent for session '{active_session_id}', prompt: '{prompt}'")

        # thread_id config enables the checkpointer to auto-load/save conversation history
        config = {"configurable": {"thread_id": active_session_id}}

        result = self.agent.invoke(
            {"messages": [HumanMessage(content=prompt)]},
            config=config,
        )
        result_messages = result.get("messages", [])

        answer_text = (
            extract_text_content(result_messages[-1].content)
            if result_messages
            else "No response generated."
        )

        return {
            "session_id": active_session_id,
            "answer": answer_text,
        }

    def stream(
        self,
        prompt: str,
        session_id: Optional[str] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Streams the Supervisor Agent execution yielding status and token chunks.

        Args:
            prompt: Natural language customer request.
            session_id: Optional session ID for multi-turn tracking.

        Yields:
            Dict event items with 'type': 'session' | 'status' | 'token'.
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        active_session_id = resolve_session_id(session_id)
        logger.info(f"Streaming Supervisor Agent for session '{active_session_id}', prompt: '{prompt}'")

        config = {"configurable": {"thread_id": active_session_id}}
        yield {"type": "session", "session_id": active_session_id}

        for mode, payload in self.agent.stream(
            {"messages": [HumanMessage(content=prompt)]},
            config=config,
            stream_mode=["updates", "messages"],
        ):
            if mode == "updates" and isinstance(payload, dict):
                if "model" in payload:
                    msgs = payload["model"].get("messages", [])
                    if msgs and hasattr(msgs[-1], "tool_calls") and msgs[-1].tool_calls:
                        for tc in msgs[-1].tool_calls:
                            yield {"type": "status", "content": get_tool_status_message(tc.get("name", ""))}
                elif "tools" in payload:
                    yield {"type": "status", "content": "Agent completed task"}

            elif mode == "messages":
                chunk = payload[0]
                if isinstance(chunk, (AIMessage, AIMessageChunk)):
                    text = extract_text_content(getattr(chunk, "content", ""))
                    if text:
                        yield {"type": "token", "content": text}


supervisor_agent = SupervisorAgent()
