from langchain_huggingface import HuggingFaceEmbeddings

MODEL_NAME = "BAAI/bge-large-en-v1.5"

# Initialize once at module level so the model
# is not reloaded on every request
embeddings_model = HuggingFaceEmbeddings(
    model_name=MODEL_NAME,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},  # recommended for BGE models
)


def embed_chunks(chunks: list[dict], cloudinary_url: str) -> list[dict]:
    """
    Takes the list of chunks from the chunker and embeds each one.

    Returns a list of Pinecone-ready vector records:
    [
        {
            "id": "uuid-chunk-0",
            "values": [0.12, 0.87, ...],   <- the embedding vector
            "metadata": {
                "text": "...",
                "filename": "report.pdf",
                "page": 1,
                "chunk_index": 0,
                "document_id": "uuid",
                "cloudinary_url": "https://..."
            }
        },
        ...
    ]

    Why we pass cloudinary_url here:
    We store it in every chunk's metadata so that if you retrieve
    a chunk later, you always know which file it came from and
    where that file lives.
    """
    texts = [chunk["text"] for chunk in chunks]

    # LangChain call — returns List[List[float]]
    vectors_list = embeddings_model.embed_documents(texts)

    vectors = []
    for i, vector in enumerate(vectors_list):
        chunk = chunks[i]
        vectors.append({
            "id": f"{chunk['document_id']}-chunk-{chunk['chunk_index']}",
            "values": vector,
            "metadata": {
                "text": chunk["text"],
                "filename": chunk["filename"],
                "page": chunk["page"],
                "chunk_index": chunk["chunk_index"],
                "document_id": chunk["document_id"],
                "cloudinary_url": cloudinary_url,
            },
        })

    return vectors