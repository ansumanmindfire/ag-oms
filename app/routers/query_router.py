import json
from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse
from app.schemas import AgentChatRequest, AgentChatResponse
from app.services.orchestration_service import OrchestrationService

router = APIRouter(prefix="/query", tags=["Agent Query"])


@router.post("", response_model=AgentChatResponse, status_code=status.HTTP_200_OK)
def query(data: AgentChatRequest):
    """Conversational endpoint for user queries (order placement, cancellation, product enquiry).

    Receives natural language prompt and optional session_id, delegates to the configured
    orchestration workflow (LangGraph or Supervisor)
    """
    result = OrchestrationService.process_query(
        prompt=data.prompt,
        session_id=data.session_id,
    )
    return AgentChatResponse(
        session_id=result["session_id"],
        answer=result["answer"],
    )


@router.post("/stream")
def query_stream(data: AgentChatRequest):
    """Server-Sent Events (SSE) streaming endpoint for agent responses.

    Streams:
    - 'session': Initial session identifier
    - 'token': Incremental tokens of the synthesized answer
    """
    def sse_event_generator():
        for event in OrchestrationService.stream_query(prompt=data.prompt, session_id=data.session_id):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

