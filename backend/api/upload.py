"""
Document upload and parsing API.

Accepts PDF, TXT, and DOCX files and returns the extracted plain text,
which the frontend populates into the project idea textarea.
"""
import io
import logging
from fastapi import APIRouter, File, UploadFile, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter()

_MAX_BYTES = 10 * 1024 * 1024  # 10 MB hard cap


def _parse_txt(data: bytes) -> str:
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not decode text file")


def _parse_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        raise HTTPException(status_code=500, detail="PDF support not installed on server")

    reader = PdfReader(io.BytesIO(data))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())
    return "\n\n".join(pages)


def _parse_docx(data: bytes) -> str:
    try:
        import docx
    except ImportError:
        raise HTTPException(status_code=500, detail="DOCX support not installed on server")

    doc = docx.Document(io.BytesIO(data))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


@router.post("/parse-document", summary="Parse uploaded document and return plain text")
async def parse_document(file: UploadFile = File(...)):
    """
    Parse a PDF, TXT, or DOCX file and return the extracted plain text.

    The frontend uses this to populate the project idea textarea so the user
    can review / edit before starting the planning pipeline.

    Raises:
        400: Unsupported file type or empty file.
        413: File exceeds the 10 MB limit.
        500: Parsing library unavailable or extraction failed.
    """
    filename = (file.filename or "").lower()

    if filename.endswith(".pdf"):
        fmt = "pdf"
    elif filename.endswith(".txt"):
        fmt = "txt"
    elif filename.endswith(".docx"):
        fmt = "docx"
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a PDF, TXT, or DOCX file.",
        )

    data = await file.read()

    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(data) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 10 MB limit.")

    try:
        if fmt == "pdf":
            text = _parse_pdf(data)
        elif fmt == "txt":
            text = _parse_txt(data)
        else:
            text = _parse_docx(data)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Document parsing failed for '%s': %s", file.filename, exc)
        raise HTTPException(status_code=500, detail=f"Failed to parse document: {exc}")

    text = text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="No text could be extracted from the file.")

    return {"text": text, "filename": file.filename, "format": fmt}
