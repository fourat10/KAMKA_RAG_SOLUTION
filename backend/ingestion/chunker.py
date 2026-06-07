from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_pages(pages: list[dict], document_id: str, filename: str) -> list[dict]:
    """
    Takes the list of pages from the extractor and splits each page's
    text into smaller chunks.

    Returns a flat list of chunks:
    [
        {
            "text": "...",
            "page": 1,
            "chunk_index": 0,
            "document_id": "uuid",
            "filename": "report.pdf"
        },
        ...
    ]

    Why these settings:
    - chunk_size 500: small enough to be specific, large enough to have context
    - chunk_overlap 50: prevents losing context at chunk boundaries
    - RecursiveCharacterTextSplitter: tries to split on paragraphs, then
      sentences, then words — respects natural text boundaries
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
    )

    # Convert pages to LangChain Document objects
    # This is the native LangChain data structure
    documents = [
        Document(
            page_content=page["text"],
            metadata={
                "page": page["page"],
                "document_id": document_id,
                "filename": filename,
            }
        )
        for page in pages
    ]

    # LangChain splits Document objects and preserves metadata
    split_docs = splitter.split_documents(documents)

    # Convert back to our flat dict format for Pinecone
    chunks = []
    for i, doc in enumerate(split_docs):
        chunks.append({
            "text": doc.page_content,
            "page": doc.metadata["page"],
            "chunk_index": i,
            "document_id": doc.metadata["document_id"],
            "filename": doc.metadata["filename"],
        })

    return chunks