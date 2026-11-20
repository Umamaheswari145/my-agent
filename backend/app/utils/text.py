import io
from pathlib import Path

from pypdf import PdfReader

from app.core.errors import AppError

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}
CONTENT_TYPE_BY_EXTENSION = {
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".md": "text/markdown",
}


def validate_upload(filename: str, size: int, max_bytes: int) -> str:
    safe_name = Path(filename).name
    suffix = Path(safe_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise AppError(
            "Only PDF, TXT, and Markdown files are supported.",
            status_code=400,
            error_code="unsupported_file",
        )
    if size <= 0:
        raise AppError("The uploaded file is empty.", status_code=400, error_code="empty_file")
    if size > max_bytes:
        raise AppError(
            f"The file exceeds the {max_bytes // (1024 * 1024)} MB upload limit.",
            status_code=413,
            error_code="file_too_large",
        )
    return suffix


def extract_text(data: bytes, suffix: str) -> str:
    if suffix == ".pdf":
        try:
            reader = PdfReader(io.BytesIO(data))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            raise AppError(
                "The PDF could not be read.", status_code=400, error_code="invalid_pdf"
            ) from None
    else:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("utf-8", errors="replace")
    text = "\n".join(line.rstrip() for line in text.splitlines())
    text = text.strip()
    if not text:
        raise AppError(
            "The document contains no extractable text.",
            status_code=400,
            error_code="empty_document",
        )
    return text


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    step = max(1, size - overlap)
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + size, len(words))
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        if end == len(words):
            break
        start += step
    return chunks
