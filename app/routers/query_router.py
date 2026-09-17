from fastapi import APIRouter, status
from app.schemas import AgentChatRequest, AgentChatResponse
from app.graph import run_oms_graph

router = APIRouter(prefix="/query", tags=["Agent Query"])


@router.post("", response_model=AgentChatResponse, status_code=status.HTTP_200_OK)
def process_query(data: AgentChatRequest):
    """Conversational endpoint for user queries (order placement, cancellation, product enquiry).

    Receives natural language prompt and optional session_id, executes the LangGraph
    StateGraph workflow with multi-turn state persistence, and returns synthesized response.
    """
    result = run_oms_graph(
        prompt=data.prompt,
        session_id=data.session_id,
    )
    return AgentChatResponse(
        session_id=result["session_id"],
        answer=result["answer"],
    )

