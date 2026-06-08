import re
from langchain_core.documents import Document


def parse_citations(answer: str, retrieved_docs: list[Document]) -> list[dict]:
    """
    Parses [1], [2]... references from the LLM answer and maps them
    back to the real chunk metadata from retrieved_docs.

    This runs entirely in Python — we never trust the LLM to produce
    accurate metadata. The [1][2] numbers are just pointers back to
    the real data we already have from the retrieval step.

    Flow:
        1. Regex finds all [N] references in the answer text
        2. Each N maps to retrieved_docs[N-1] (1-indexed)
        3. We pull filename, page, excerpt from the real Document metadata
        4. Return a clean list of citation objects for the frontend

    Args:
        answer: the final answer string produced by the LLM
        retrieved_docs: the list of Document objects returned by retrieve_context

    Returns:
        List of citation dicts, one per unique [N] reference found in the answer:
        [
            {
                "reference": "[1]",
                "filename": "report.pdf",
                "page": 5,
                "chunk_index": 23,
                "excerpt": "In Q3 the company recorded..."
            },
            ...
        ]
    """
    if not retrieved_docs:
        return []

    # Find all [1], [2], [3]... in the answer
    found_refs = re.findall(r'\[(\d+)\]', answer)

    if not found_refs:
        return []

    # Deduplicate while preserving first-occurrence order
    seen = set()
    unique_refs = []
    for ref in found_refs:
        if ref not in seen:
            seen.add(ref)
            unique_refs.append(ref)

    citations = []
    for ref in unique_refs:
        index = int(ref) - 1  # [1] → index 0, [2] → index 1

        # Guard against the LLM hallucinating a reference number that doesn't exist
        if 0 <= index < len(retrieved_docs):
            doc = retrieved_docs[index]
            citations.append({
                "reference": f"[{ref}]",
                "filename": doc.metadata.get("filename", "Unknown"),
                "page": doc.metadata.get("page", None),
                "chunk_index": doc.metadata.get("chunk_index", None),
                "excerpt": doc.page_content[:300],
            })

    return citations