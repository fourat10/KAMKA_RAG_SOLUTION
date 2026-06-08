import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.tools import tool

MODEL_NAME = "BAAI/bge-large-en-v1.5"

embeddings_model = HuggingFaceEmbeddings(
    model_name=MODEL_NAME,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)

vectorstore = PineconeVectorStore(
    index_name=os.getenv("PINECONE_INDEX_NAME"),
    embedding=embeddings_model,
)


def make_summarize_tool(document_ids: list[str]):
    """
    Factory function that returns a summarize_document tool scoped
    to the given document_ids.

    The document_ids list is captured in the closure and used as a
    security check — the LLM can only summarize documents the user
    explicitly selected, never arbitrary documents.
    """

    @tool
    def summarize_document(document_id: str) -> str:
        """
        Fetch the complete content of a specific document and prepare it
        for summarization. Unlike retrieve_context which does semantic search,
        this tool retrieves ALL chunks of a document in reading order.

        Use this tool when:
        - The user asks to summarize a document
        - The user wants to know what a document is about in general
        - The user asks for the main points of a document
        - The user says give me an overview of this document

        Do NOT use this tool when:
        - The user asks a specific question about document content (use retrieve_context instead)
        - The user asks to calculate something (use calculator instead)
        - The user is making casual conversation

        Args:
            document_id: the exact ID of the document to summarize.
                         Must be one of the document IDs provided in the conversation.

        Returns:
            The full text content of the document ordered by page number.
        """
        # Security check — never allow summarizing a document outside the selected list
        # document_ids is captured from the closure, the LLM cannot override this
        if document_id not in document_ids:
            return (
                f"Access denied: document '{document_id}' was not selected "
                f"for this conversation. Available document IDs: {', '.join(document_ids)}"
            )

        try:
            # Use a dummy vector to fetch ALL chunks from this document's namespace
            # We want everything in reading order, not just semantically similar chunks
            dummy_vector = [0.0] * 1024  # matches BAAI/bge-large-en-v1.5 dimension

            index = vectorstore._index
            raw_results = index.query(
                vector=dummy_vector,
                top_k=200,       # fetch up to 200 chunks — enough for any document
                filter={"document_id": {"$eq": document_id}},
                include_metadata=True,
            )

            if not raw_results["matches"]:
                return (
                    f"No content found for document ID: {document_id}. "
                    f"The document may have been deleted or not yet processed."
                )

            # Sort by page then chunk_index to restore original reading order
            matches = sorted(
                raw_results["matches"],
                key=lambda m: (
                    m["metadata"].get("page", 0),
                    m["metadata"].get("chunk_index", 0),
                ),
            )

            filename = matches[0]["metadata"].get("filename", "Unknown document")
            total_chunks = len(matches)

            # Concatenate all chunks in reading order
            full_text = "\n\n".join(
                m["metadata"].get("text", "") for m in matches
            )

            return (
                f"Document: {filename}\n"
                f"Total chunks: {total_chunks}\n\n"
                f"Full content:\n{full_text}"
            )

        except Exception as e:
            return f"Error fetching document content: {str(e)}"

    return summarize_document