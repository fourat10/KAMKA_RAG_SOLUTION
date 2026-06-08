import os
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain.tools import tool

MODEL_NAME = "BAAI/bge-large-en-v1.5"

# Initialize once at module level — cached after first load
embeddings_model = HuggingFaceEmbeddings(
    model_name=MODEL_NAME,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)


def get_index():
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    return pc.Index(os.getenv("PINECONE_INDEX_NAME", "documents"))


def make_retrieve_tool(document_ids: list[str]):
    """
    Factory function that returns a retrieve_context tool scoped
    to the given document_ids via Pinecone metadata filter.

    Uses the raw Pinecone SDK directly instead of LangChain's
    PineconeVectorStore wrapper — more reliable filter behavior.
    """

    @tool(response_format="content_and_artifact")
    def retrieve_context(query: str):
        """
        Search the content of the selected documents to find information
        relevant to the user's question.

        Use this tool when:
        - The user asks a factual question about the content of a document
        - The user wants to know what a document says about a specific topic
        - The answer requires reading or extracting information from a file
        - The user asks questions like "what does the document say about X?"

        Do NOT use this tool when:
        - The user sends a greeting (Hello, Hi, Thanks)
        - The user asks to calculate something (use calculator instead)
        - The user asks for a full summary (use summarize_document instead)

        Always cite sources as [1], [2]... inline in your answer.

        Args:
            query: the user's question in natural language
        """
        # BGE models perform better with this prefix on queries
        prefixed_query = (
            f"Represent this sentence for searching relevant passages: {query}"
        )

        # Embed the query using the same model used during ingestion
        query_vector = embeddings_model.embed_query(prefixed_query)

        # Query Pinecone directly with metadata filter
        index = get_index()
        results = index.query(
            vector=query_vector,
            top_k=5,
            filter={"document_id": {"$in": document_ids}},
            include_metadata=True,
        )

        if not results["matches"]:
            return "No relevant information found in the selected documents.", []

        # Convert raw Pinecone results to LangChain Document objects
        docs = []
        for match in results["matches"]:
            metadata = match.get("metadata", {})
            text = metadata.get("text", "")
            docs.append(Document(
                page_content=text,
                metadata={
                    "filename": metadata.get("filename", "Unknown"),
                    "page": metadata.get("page", None),
                    "chunk_index": metadata.get("chunk_index", None),
                    "document_id": metadata.get("document_id", ""),
                    "cloudinary_url": metadata.get("cloudinary_url", ""),
                }
            ))

        # Format as numbered context so the LLM can reference [1], [2] in its answer
        serialized = "\n\n".join(
            f"[{i+1}] (Source: {doc.metadata.get('filename', 'Unknown')}, "
            f"Page: {doc.metadata.get('page', '?')})\n{doc.page_content}"
            for i, doc in enumerate(docs)
        )

        return serialized, docs

    return retrieve_context