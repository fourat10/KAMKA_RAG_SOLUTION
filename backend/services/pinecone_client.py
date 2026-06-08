import os
from pinecone import Pinecone


def get_index():
    """
    Returns the Pinecone index object.
    Call this inside each function that needs Pinecone
    so the connection is always fresh.
    """
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = os.getenv("PINECONE_INDEX_NAME", "documents")
    return pc.Index(index_name)


def upsert_chunks(document_id: str, vectors: list[dict]):
    """
    Upserts a list of vector records into the document's namespace.

    Each item in vectors must be:
    {
        "id": "document_id-chunk-0",
        "values": [0.12, 0.87, ...],
        "metadata": {
            "text": "...",
            "filename": "report.pdf",
            "page": 1,
            "chunk_index": 0,
            "document_id": "uuid",
            "cloudinary_url": "https://..."
        }
    }
    """
    index = get_index()
    index.upsert(vectors=vectors)


def delete_document_vectors(document_id: str):
    """
    Deletes all vectors for a document from the default namespace.
    """
    index = get_index()
    index.delete(filter={"document_id": {"$eq": document_id}})
