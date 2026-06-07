import fitz  # PyMuPDF


def extract_text(file_bytes: bytes, filename: str) -> list[dict]:
    """
    Extracts text from a PDF or TXT file.

    Returns a list of pages:
    [
        { "page": 1, "text": "..." },
        { "page": 2, "text": "..." },
        ...
    ]

    For TXT files there is only one "page" (page 1).
    Page numbers are kept here because citations need them later.
    """
    if filename.lower().endswith(".pdf"):
        return _extract_from_pdf(file_bytes)
    elif filename.lower().endswith(".txt"):
        return _extract_from_txt(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {filename}")


def _extract_from_pdf(file_bytes: bytes) -> list[dict]:
    """
    Opens the PDF from bytes (no disk write needed) and extracts
    text page by page using PyMuPDF.
    """
    pages = []
    # fitz.open with stream= reads from bytes directly
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text().strip()
        if text:  # skip empty pages
            pages.append({"page": page_num, "text": text})
    doc.close()
    return pages


def _extract_from_txt(file_bytes: bytes) -> list[dict]:
    """
    Decodes TXT bytes and returns as a single page.
    """
    text = file_bytes.decode("utf-8", errors="ignore").strip()
    return [{"page": 1, "text": text}]