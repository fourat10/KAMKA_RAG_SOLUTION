import os
from pymongo import MongoClient
from datetime import datetime, timezone


def get_collection():
    """
    Returns the 'documents' collection from MongoDB Atlas.
    MongoClient handles connection pooling — safe to call on every request.
    """
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client[os.getenv("MONGODB_DB_NAME", "kamka")]
    return db["documents"]


def insert_document(
    document_id: str,
    filename: str,
    cloudinary_url: str,
    cloudinary_public_id: str,
    chunk_count: int,
):
    """
    Inserts a new document record into MongoDB.
    Uses document_id as the _id so it matches the Pinecone namespace
    and Cloudinary public_id — one ID ties everything together.
    """
    collection = get_collection()
    collection.insert_one({
        "_id": document_id,
        "filename": filename,
        "cloudinary_url": cloudinary_url,
        "cloudinary_public_id": cloudinary_public_id,
        "chunk_count": chunk_count,
        "uploaded_at": datetime.now(timezone.utc),
    })


def get_all_documents() -> list[dict]:
    """
    Returns all document records, newest first.
    Renames _id to document_id for cleaner API responses.
    """
    collection = get_collection()
    docs = list(collection.find().sort("uploaded_at", -1))
    for doc in docs:
        doc["document_id"] = str(doc.pop("_id"))
    return docs


def get_document(document_id: str) -> dict | None:
    """
    Returns a single document record by its ID, or None if not found.
    """
    collection = get_collection()
    doc = collection.find_one({"_id": document_id})
    if doc:
        doc["document_id"] = str(doc.pop("_id"))
    return doc


def delete_document(document_id: str):
    """
    Deletes a document record from MongoDB by its ID.
    """
    collection = get_collection()
    collection.delete_one({"_id": document_id})