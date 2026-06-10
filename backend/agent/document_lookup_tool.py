from langchain.tools import tool
from services.mongodb_client import get_collection


def make_document_lookup_tool(document_ids: list[str]):
    """
    Factory function that returns a document_lookup tool scoped
    to the given document_ids.

    The tool fetches filenames from MongoDB for the selected documents
    so the LLM can map a filename the user mentions to the correct document_id.
    """

    @tool
    def document_lookup(filename: str = "") -> str:
        """
        Look up document IDs and their corresponding filenames for
        the documents selected in this conversation.

        Use this tool when:
        - The user mentions a specific filename (e.g. "summarize file1.txt")
        - You need to find the document_id that corresponds to a filename
        - You are unsure which document_id matches what the user is referring to
        - Before calling summarize_document, if the user referred to a file by name

        Always call this tool first when the user mentions a filename,
        then use the returned document_id to call summarize_document.

        Args:
            filename: optional filename to search for (e.g. "file1.txt").
                      If empty, returns all documents in this conversation.

        Returns:
            A list of available documents with their document_id and filename.
        """
        try:
            collection = get_collection("documents")

            # Fetch only the documents selected for this conversation
            docs = list(collection.find(
                {"_id": {"$in": document_ids}},
                {"_id": 1, "filename": 1}  # only fetch id and filename
            ))

            if not docs:
                return "No documents found for this conversation."

            # If a filename was provided, try to find a match
            if filename.strip():
                filename_lower = filename.strip().lower()
                matches = [
                    d for d in docs
                    if filename_lower in d["filename"].lower()
                ]
                if matches:
                    result = "\n".join(
                        f'- filename: "{d["filename"]}" → document_id: "{d["_id"]}"'
                        for d in matches
                    )
                    return f"Found matching document(s):\n{result}"
                else:
                    # No exact match — return all so the LLM can pick the closest
                    all_docs = "\n".join(
                        f'- filename: "{d["filename"]}" → document_id: "{d["_id"]}"'
                        for d in docs
                    )
                    return (
                        f'No document found with filename "{filename}".\n'
                        f"Available documents in this conversation:\n{all_docs}"
                    )

            # No filename provided — return all documents
            all_docs = "\n".join(
                f'- filename: "{d["filename"]}" → document_id: "{d["_id"]}"'
                for d in docs
            )
            return f"Available documents in this conversation:\n{all_docs}"

        except Exception as e:
            return f"Error looking up documents: {str(e)}"

    return document_lookup