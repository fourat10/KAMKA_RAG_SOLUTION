from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from agent.agent import run_agent
from services.mongodb_client import get_document

router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    document_ids: list[str]
    user_id: str

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


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Receives a user query, verifies document ownership, runs the agent,
    and returns the answer with structured citations.
    """

    # --- Verify every document_id belongs to this user ---
    # This prevents a user from querying another user's documents
    # even if they know the document_id
    for doc_id in request.document_ids:
        doc = get_document(document_id=doc_id, user_id=request.user_id)
        if not doc:
            raise HTTPException(
                status_code=403,
                detail=f"Document '{doc_id}' not found or does not belong to this user."
            )

    # --- Inject document_ids into the query ---
    # The agent needs to know which document IDs are available so it can
    # pass the correct one to summarize_document when needed.
    # We append this context to the query — invisible to the user but
    # visible to the LLM so it knows exactly which IDs to use.
    doc_ids_str = ", ".join(request.document_ids)
    enriched_query = (
        f"{request.query}\n\n"
        f"[Available document IDs for this conversation: {doc_ids_str}]"
    )

    try:
        result = run_agent(
            query=enriched_query,
            document_ids=request.document_ids,
        )

        return ChatResponse(
            answer=result["answer"],
            citations=result["citations"],
            used_retrieval=len(result["citations"]) > 0,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent failed: {str(e)}"
        )