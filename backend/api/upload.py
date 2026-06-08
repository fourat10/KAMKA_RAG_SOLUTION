import uuid
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ingestion.chunker import chunk_pages
from ingestion.embedder import embed_chunks
from ingestion.extractor import extract_text
from models.response_models import DocumentRecord, UploadResponse
from services.cloudinary_client import delete_file, upload_file
from services.mongodb_client import (
    delete_document,
    get_document,
    get_user_documents,
    insert_document,
)
from services.pinecone_client import delete_document_vectors, upsert_chunks

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".txt"}
MAX_FILE_SIZE_MB = 20


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Form(...),
):
    """
    Receives a PDF or TXT file and a user_id, runs the full ingestion pipeline,
    and stores the document tagged to that user.
    """
    filename = file.filename or ""
    extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{extension}'. Only PDF and TXT are allowed.",
        )

    file_bytes = await file.read()

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f} MB). Maximum is {MAX_FILE_SIZE_MB} MB.",
        )

    if not user_id.strip():
        raise HTTPException(status_code=400, detail="user_id cannot be empty.")

    document_id = str(uuid.uuid4())

    try:
        logger.info(f"[{user_id}] Starting upload for document: {filename}")
        
        pages = extract_text(file_bytes, filename)
        logger.info(f"[{user_id}] Extracted {len(pages)} pages")

        if not pages:
            raise HTTPException(
                status_code=422,
                detail="Could not extract any text from the file. It may be scanned or empty.",
            )

        chunks = chunk_pages(pages, document_id, filename)
        logger.info(f"[{user_id}] Created {len(chunks)} chunks")

        cloudinary_result = upload_file(file_bytes, document_id, filename)
        cloudinary_url = cloudinary_result["secure_url"]
        cloudinary_public_id = cloudinary_result["public_id"]
        logger.info(f"[{user_id}] Uploaded to Cloudinary: {cloudinary_url}")

        vectors = embed_chunks(chunks, cloudinary_url)
        logger.info(f"[{user_id}] Generated {len(vectors)} embeddings")
        
        upsert_chunks(document_id, vectors)
        logger.info(f"[{user_id}] Stored vectors in Pinecone")

        uploaded_at = datetime.now(timezone.utc)
        insert_document(
            document_id=document_id,
            filename=filename,
            cloudinary_url=cloudinary_url,
            cloudinary_public_id=cloudinary_public_id,
            chunk_count=len(chunks),
            user_id=user_id.strip(),
        )
        logger.info(f"[{user_id}] Saved document to MongoDB: {document_id}")

        return UploadResponse(
            document_id=document_id,
            filename=filename,
            chunk_count=len(chunks),
            cloudinary_url=cloudinary_url,
            uploaded_at=uploaded_at,
        )

    except HTTPException:
        logger.error(f"[{user_id}] HTTP Exception: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"[{user_id}] Ingestion failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}",
        )


@router.get("/documents", response_model=list[DocumentRecord])
def list_documents(user_id: str):
    """
    Returns the current user's uploaded documents, newest first.
    """
    if not user_id.strip():
        raise HTTPException(status_code=400, detail="user_id cannot be empty.")

    try:
        return get_user_documents(user_id.strip())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch documents: {str(e)}",
        )


@router.delete("/documents/{document_id}")
def remove_document(document_id: str, user_id: str):
    """
    Deletes a document owned by the current user from Cloudinary, Pinecone,
    and MongoDB.
    """
    if not user_id.strip():
        raise HTTPException(status_code=400, detail="user_id cannot be empty.")

    doc = get_document(document_id=document_id, user_id=user_id.strip())
    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Document not found or does not belong to this user.",
        )

    try:
        public_id = doc.get("cloudinary_public_id")
        if public_id:
            delete_file(public_id)

        delete_document_vectors(document_id)
        deleted = delete_document(document_id=document_id, user_id=user_id.strip())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}",
        )

    if not deleted:
        raise HTTPException(status_code=404, detail="Document was not deleted.")

    return {"deleted": True, "document_id": document_id}
