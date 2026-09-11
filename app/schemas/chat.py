"""Pydantic V2 schemas for Agent Chat interaction requests and responses."""

from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    """Request schema for sending a prompt to the Master Orchestrator Agent."""

    prompt: str = Field(..., min_length=1, description="Natural language customer request")
    session_id: Optional[str] = Field(None, description="Optional existing session ID for conversation context")


class AgentChatResponse(BaseModel):
    """Response schema returned by the Master Orchestrator Agent."""

    session_id: str = Field(..., description="Chat session ID")
    answer: str = Field(..., description="Synthesized AI agent response")


