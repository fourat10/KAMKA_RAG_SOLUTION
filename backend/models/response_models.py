from pydantic import BaseModel
from datetime import datetime


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    chunk_count: int
    cloudinary_url: str
    uploaded_at: datetime


class DocumentRecord(BaseModel):
    document_id: str
    filename: str
    cloudinary_url: str
    uploaded_at: datetime
    chunk_count: int