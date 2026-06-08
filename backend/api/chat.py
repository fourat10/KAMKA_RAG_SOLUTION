from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from agent.agent import run_agent
from services.mongodb_client import get_document
from services.memory import get_history, save_turn

router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    document_ids: list[str]
    user_id: str
    session_id: str

    @field_validator("query")
    @classmethod
    def query_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Query cannot be empty.")
        return v.strip()

    @field_validator("document_ids")
    @classmethod
    def document_ids_must_not_be_empty(cls, v):
        if not v:
            raise ValueError("At least one document_id must be provided.")
        return v

    @field_validator("user_id")
    @classmethod
    def user_id_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("user_id cannot be empty.")
        return v.strip()

    @field_validator("session_id")
    @classmethod
    def session_id_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("session_id cannot be empty.")
        return v.strip()


class CitationResponse(BaseModel):
    reference: str
    filename: str
    page: int | None
    chunk_index: int | None
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[CitationResponse]
    used_retrieval: bool
    session_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Receives a user query, loads conversation history from MongoDB,
    runs the agent with history context, saves the turn, and returns
    the answer with structured citations.
    """

    # --- Verify every document_id belongs to this user ---
    for doc_id in request.document_ids:
        doc = get_document(document_id=doc_id, user_id=request.user_id)
        if not doc:
            raise HTTPException(
                status_code=403,
                detail=f"Document '{doc_id}' not found or does not belong to this user."
            )

    # --- Load conversation history from MongoDB ---
    history = get_history(session_id=request.session_id, limit=10)

    # --- DEBUG PRINTS ---
    print(f"\n{'='*60}")
    print(f"  SESSION ID : {request.session_id}")
    print(f"  QUERY      : {request.query}")
    print(f"  HISTORY    : {len(history)} messages loaded")
    for i, msg in enumerate(history):
        preview = msg['content'][:80].replace('\n', ' ')
        print(f"    [{i}] {msg['role']}: {preview}")
    print(f"{'='*60}\n")

    # --- Inject document_ids into the query ---
    doc_ids_str = ", ".join(request.document_ids)
    enriched_query = (
        f"{request.query}\n\n"
        f"[Available document IDs for this conversation: {doc_ids_str}]"
    )

    try:
        result = run_agent(
            query=enriched_query,
            document_ids=request.document_ids,
            history=history,
        )

        # --- Save this turn to MongoDB ---
        save_turn(
            session_id=request.session_id,
            user_message=request.query,
            assistant_answer=result["answer"],
        )

        return ChatResponse(
            answer=result["answer"],
            citations=result["citations"],
            used_retrieval=len(result["citations"]) > 0,
            session_id=request.session_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent failed: {str(e)}"
        )