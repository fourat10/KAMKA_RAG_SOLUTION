import os
from pymongo import MongoClient
from datetime import datetime, timezone


def get_collection():
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client[os.getenv("MONGODB_DB_NAME", "kamka")]
    return db["documents"]


def insert_document(
    document_id: str,
    filename: str,
    cloudinary_url: str,
    cloudinary_public_id: str,
    chunk_count: int,
    user_id: str,
    ):
    collection = get_collection()
    collection.insert_one({
        "_id": document_id,
        "filename": filename,
        "cloudinary_url": cloudinary_url,
        "cloudinary_public_id": cloudinary_public_id,
        "chunk_count": chunk_count,
        "user_id": user_id,
        "uploaded_at": datetime.now(timezone.utc),
    })


def get_user_documents(user_id: str) -> list[dict]:
    """
    Returns all documents belonging to a specific user, newest first.
    """
    collection = get_collection()
    docs = list(collection.find({"user_id": user_id}).sort("uploaded_at", -1))
    for doc in docs:
        doc["document_id"] = str(doc.pop("_id"))
    return docs


def get_document(document_id: str, user_id: str) -> dict | None:
    """
    Returns a document only if it belongs to the given user.
    """
    collection = get_collection()
    doc = collection.find_one({"_id": document_id, "user_id": user_id})
    if doc:
        doc["document_id"] = str(doc.pop("_id"))
    return doc


def delete_document(document_id: str, user_id: str) -> bool:
    """
    Deletes a document only if it belongs to the given user.
    Returns True if deleted, False if not found or not owned by user.
    """
    collection = get_collection()
    result = collection.delete_one({"_id": document_id, "user_id": user_id})
    return result.deleted_count > 0