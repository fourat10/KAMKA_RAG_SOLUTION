import os
from fastapi import APIRouter
from pinecone import Pinecone
from services.mongodb_client import get_collection

router = APIRouter()

@router.get("/debug/pinecone/{document_id}")
def debug_pinecone(document_id: str):
    """
    Temporary debug endpoint — remove before submission.
    Fetches vectors from Pinecone filtered by document_id metadata
    and returns the raw results so we can verify what's stored.
    """
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(os.getenv("PINECONE_INDEX_NAME", "documents"))

    # Query with a dummy vector and filter by document_id
    dummy_vector = [0.0] * 1024

    # Try with metadata filter
    results_filtered = index.query(
        vector=dummy_vector,
        top_k=3,
        filter={"document_id": {"$eq": document_id}},
        include_metadata=True,
    )

    # Also try without filter to see what's in the index at all
    results_all = index.query(
        vector=dummy_vector,
        top_k=3,
        include_metadata=True,
    )

    return {
        "filtered_results": {
            "count": len(results_filtered["matches"]),
            "matches": [
                {
                    "id": m["id"],
                    "metadata": m["metadata"],
                }
                for m in results_filtered["matches"]
            ]
        },
        "all_results_sample": {
            "count": len(results_all["matches"]),
            "matches": [
                {
                    "id": m["id"],
                    "metadata": m["metadata"],
                }
                for m in results_all["matches"]
            ]
        }
    }


@router.get("/debug/mongodb/{user_id}")
def debug_mongodb(user_id: str):
    """
    Debug endpoint to check what documents are stored in MongoDB for a user.
    """
    collection = get_collection()
    docs = list(collection.find({"user_id": user_id}))
    
    return {
        "user_id": user_id,
        "document_count": len(docs),
        "documents": [
            {
                "document_id": doc.get("_id"),
                "filename": doc.get("filename"),
                "user_id": doc.get("user_id"),
                "chunk_count": doc.get("chunk_count"),
                "uploaded_at": str(doc.get("uploaded_at")),
            }
            for doc in docs
        ]
    }