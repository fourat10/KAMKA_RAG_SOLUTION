import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator
from agent.agent import run_agent_stream
from services.mongodb_client import get_document
from services.memory import get_history, save_turn

router = APIRouter()


class StreamRequest(BaseModel):
    query: str
    document_ids: list[str]
    user_id: str
    session_id: str

    @field_validator("query")
    @classmethod
    def query_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be empty.")
        return v.strip()

    @field_validator("document_ids")
    @classmethod
    def ids_not_empty(cls, v):
        if not v:
            raise ValueError("At least one document_id must be provided.")
        return v

    @field_validator("user_id")
    @classmethod
    def user_id_not_empty(cls, v):
        if not v.strip():
            raise ValueError("user_id cannot be empty.")
        return v.strip()

    @field_validator("session_id")
    @classmethod
    def session_id_not_empty(cls, v):
        if not v.strip():
            raise ValueError("session_id cannot be empty.")
        return v.strip()


def format_sse(data: dict) -> str:
    """
    Format a dict as a Server-Sent Events (SSE) message.
    SSE format: "data: {json}\n\n"
    The double newline signals the end of one event to the client.
    """
    return f"data: {json.dumps(data)}\n\n"


@router.post("/chat/stream")
async def chat_stream(request: StreamRequest):
    """
    Streaming version of the chat endpoint.
    Returns a StreamingResponse with Server-Sent Events.

    Event types:
    - {"type": "token", "content": "..."}  — one per streamed word/token
    - {"type": "citations", "data": [...]}  — sent after all tokens
    - {"type": "done"}                      — signals end of stream
    - {"type": "error", "content": "..."}   — on failure
    """

    # --- Verify document ownership ---
    for doc_id in request.document_ids:
        doc = get_document(document_id=doc_id, user_id=request.user_id)
        if not doc:
            raise HTTPException(
                status_code=403,
                detail=f"Document '{doc_id}' not found or does not belong to this user."
            )

    # --- Load history ---
    history = get_history(session_id=request.session_id, limit=10)

    # --- Inject document_ids into query ---
    doc_ids_str = ", ".join(request.document_ids)
    enriched_query = (
        f"{request.query}\n\n"
        f"[Available document IDs for this conversation: {doc_ids_str}]"
    )

    async def event_generator():
        try:
            # Run the full agent and stream the answer
            async for event in run_agent_stream(
                query=enriched_query,
                document_ids=request.document_ids,
                history=history,
            ):
                if event["type"] == "done":
                    # Save turn to MongoDB when agent finishes
                    save_turn(
                        session_id=request.session_id,
                        user_message=request.query,
                        assistant_answer=event["answer"],
                    )
                    # Send citations
                    yield format_sse({
                        "type": "citations",
                        "data": event["citations"],
                    })
                    # Send done signal
                    yield format_sse({"type": "done"})
                else:
                    # Stream token
                    yield format_sse(event)

        except Exception as e:
            yield format_sse({"type": "error", "content": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            # Prevent buffering — essential for streaming to work
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )