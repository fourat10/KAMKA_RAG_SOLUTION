import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, HTTPException

from ingestion.extractor import extract_text
from ingestion.chunker import chunk_pages
from ingestion.embedder import embed_chunks
from services.pinecone_client import upsert_chunks
from services.cloudinary_client import upload_file
from services.mongodb_client import insert_document
from models.response_models import UploadResponse

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".txt"}
MAX_FILE_SIZE_MB = 20


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Receives a PDF or TXT file and runs the full ingestion pipeline:
    1. Validate file type and size
    2. Read file bytes into memory (no disk write)
    3. Extract text page by page
    4. Chunk the text
    5. Embed the chunks
    6. Upsert vectors to Pinecone
    7. Upload raw file to Cloudinary
    8. Save document record to MongoDB
    9. Return the document record to the frontend
    """

    # --- Validation ---
    filename = file.filename or ""
    extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{extension}'. Only PDF and TXT are allowed."
        )

    # Read all bytes into memory once
    file_bytes = await file.read()

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f} MB). Maximum is {MAX_FILE_SIZE_MB} MB."
        )

    # Generate a unique ID for this document
    # This same ID is used as:
    # - Pinecone namespace
    # - Cloudinary public_id prefix
    # - MongoDB _id
    document_id = str(uuid.uuid4())

    try:
        # --- Step 1: Extract text from bytes ---
        # No disk write — PyMuPDF reads directly from bytes
        pages = extract_text(file_bytes, filename)

        if not pages:
            raise HTTPException(
                status_code=422,
                detail="Could not extract any text from the file. It may be scanned or empty."
            )

        # --- Step 2: Chunk the pages ---
        chunks = chunk_pages(pages, document_id, filename)

        # --- Step 3: Upload raw file to Cloudinary ---
        # We do this before embedding so we have the cloudinary_url
        # to store inside each chunk's Pinecone metadata
        cloudinary_result = upload_file(file_bytes, document_id, filename)
        cloudinary_url = cloudinary_result["secure_url"]
        cloudinary_public_id = cloudinary_result["public_id"]

        # --- Step 4: Embed chunks ---
        vectors = embed_chunks(chunks, cloudinary_url)

        # --- Step 5: Upsert to Pinecone ---
        # namespace = document_id keeps this document's chunks isolated
        upsert_chunks(document_id, vectors)

        # --- Step 6: Save document record to MongoDB ---
        uploaded_at = datetime.now(timezone.utc)
        insert_document(
            document_id=document_id,
            filename=filename,
            cloudinary_url=cloudinary_url,
            cloudinary_public_id=cloudinary_public_id,
            chunk_count=len(chunks),
        )

        return UploadResponse(
            document_id=document_id,
            filename=filename,
            chunk_count=len(chunks),
            cloudinary_url=cloudinary_url,
            uploaded_at=uploaded_at,
        )

    except HTTPException:
        raise  # re-raise validation errors as-is

    except Exception as e:
        # Catch unexpected errors (Pinecone down, OpenAI rate limit, etc.)
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}"
        )