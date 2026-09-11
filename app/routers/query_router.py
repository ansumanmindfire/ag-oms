"""FastAPI APIRouter for agent query and conversational interaction endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import AgentChatRequest, AgentChatResponse
from app.agents import master_orchestrator

router = APIRouter(prefix="/query", tags=["Agent Query"])


@router.post("", response_model=AgentChatResponse, status_code=status.HTTP_200_OK)
def process_query(data: AgentChatRequest, db: Session = Depends(get_db)):
    """Conversational endpoint for user queries (order placement, cancellation, product enquiry).

    Receives natural language prompt and optional session_id, runs Master Orchestrator,
    and returns synthesized response + execution details.
    """
    result = master_orchestrator.run(
        prompt=data.prompt,
        db=db,
        session_id=data.session_id,
    )
    return AgentChatResponse(
        session_id=result["session_id"],
        answer=result["answer"],
    )



