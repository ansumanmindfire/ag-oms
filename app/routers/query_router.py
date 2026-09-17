from fastapi import APIRouter, status
from app.schemas import AgentChatRequest, AgentChatResponse
from app.services.orchestration_service import process_query

router = APIRouter(prefix="/query", tags=["Agent Query"])


@router.post("", response_model=AgentChatResponse, status_code=status.HTTP_200_OK)
def query(data: AgentChatRequest):
    """Conversational endpoint for user queries (order placement, cancellation, product enquiry).

    Receives natural language prompt and optional session_id, delegates to the configured
    orchestration workflow (LangGraph or Supervisor)
    """
    result = process_query(
        prompt=data.prompt,
        session_id=data.session_id,
    )
    return AgentChatResponse(
        session_id=result["session_id"],
        answer=result["answer"],
    )
