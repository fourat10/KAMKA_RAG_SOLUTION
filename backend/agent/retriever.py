import os
import cohere
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


def rerank(query: str, docs: list[Document], top_n: int = 5) -> list[Document]:
    """
    Uses Cohere's rerank API to re-score documents by true relevance
    to the query, not just vector similarity.

    Takes up to 20 candidate docs from Pinecone and returns the top_n
    most relevant ones according to the cross-encoder model.

    If COHERE_API_KEY is not set, falls back to returning docs as-is.
    """
    cohere_key = os.getenv("COHERE_API_KEY")
    if not cohere_key or not docs:
        # Graceful fallback — reranking is optional
        return docs[:top_n]

    try:
        co = cohere.Client(cohere_key)

        # Cohere expects plain strings
        passages = [doc.page_content for doc in docs]

        response = co.rerank(
            model="rerank-english-v3.0",   # best model for English
            query=query,
            documents=passages,
            top_n=top_n,
        )

        # Map Cohere results back to Document objects
        # response.results is sorted by relevance score descending
        reranked_docs = []
        for result in response.results:
            doc = docs[result.index]
            # Attach the relevance score to metadata for transparency
            doc.metadata["rerank_score"] = round(result.relevance_score, 4)
            reranked_docs.append(doc)

        return reranked_docs

    except Exception as e:
        # If Cohere fails for any reason, fall back to original order
        print(f"Reranking failed, using original order: {e}")
        return docs[:top_n]


def make_retrieve_tool(document_ids: list[str]):
    """
    Factory function that returns a retrieve_context tool scoped
    to the given document_ids via Pinecone metadata filter.

    Retrieval pipeline:
    1. Embed the query with BGE prefix
    2. Retrieve top 20 candidates from Pinecone
    3. Rerank with Cohere cross-encoder
    4. Return top 5 by relevance score
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

        # Embed the query
        query_vector = embeddings_model.embed_query(prefixed_query)

        # Step 1 — Retrieve more candidates than needed (20 instead of 5)
        # The reranker will pick the best 5 from these 20
        index = get_index()
        results = index.query(
            vector=query_vector,
            top_k=20,
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
                    "pinecone_score": round(match.get("score", 0), 4),
                }
            ))

        # Step 2 — Rerank with Cohere, keep top 5
        # Uses the original unprefixed query for reranking
        # (the prefix is only for the embedding model, not the reranker)
        reranked = rerank(query=query, docs=docs, top_n=5)

        # Format as numbered context so the LLM can reference [1], [2]
        serialized = "\n\n".join(
            f"[{i+1}] (Source: {doc.metadata.get('filename', 'Unknown')}, "
            f"Page: {doc.metadata.get('page', '?')})\n{doc.page_content}"
            for i, doc in enumerate(reranked)
        )

        return serialized, reranked

    return retrieve_context