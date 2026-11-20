import logging
from pathlib import Path
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.constants import DOCUMENT_STATUS_READY
from app.core.errors import AppError
from app.llm.base import LLMProvider
from app.llm.errors import ProviderError
from app.models import Document, DocumentChunk, User
from app.schemas.document import DocumentSearchResult
from app.utils.text import (
    CONTENT_TYPE_BY_EXTENSION,
    chunk_text,
    extract_text,
    validate_upload,
)
from app.utils.vector import cosine_similarity, keyword_score

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def list(self, db: Session, user: User, limit: int, offset: int) -> tuple[list[Document], int]:
        total = (
            db.scalar(select(func.count()).select_from(Document).where(Document.user_id == user.id))
            or 0
        )
        items = list(
            db.scalars(
                select(Document)
                .where(Document.user_id == user.id)
                .order_by(Document.created_at.desc(), Document.id.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        return items, total

    def get(self, db: Session, user: User, document_id) -> Document:
        document = db.scalar(
            select(Document).where(Document.id == document_id, Document.user_id == user.id)
        )
        if document is None:
            raise AppError("Document not found.", status_code=404, error_code="not_found")
        return document

    async def upload(
        self,
        db: Session,
        user: User,
        *,
        filename: str,
        data: bytes,
        provider: LLMProvider | None = None,
    ) -> Document:
        suffix = validate_upload(filename, len(data), self._settings.max_upload_bytes)
        safe_name = Path(filename).name[:255]
        upload_dir = Path(self._settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        storage_path = upload_dir / f"{uuid4()}{suffix}"
        storage_path.write_bytes(data)

        document = Document(
            user_id=user.id,
            filename=safe_name,
            content_type=CONTENT_TYPE_BY_EXTENSION[suffix],
            size_bytes=len(data),
            storage_path=str(storage_path),
            status="processing",
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        try:
            await self._index(db, document, suffix, provider)
        except AppError as exc:
            document.status = "failed"
            document.error_message = exc.detail
            db.commit()
            raise
        except Exception:
            logger.exception("Document indexing failed for %s", document.id)
            document.status = "failed"
            document.error_message = "The document could not be processed."
            db.commit()
        db.refresh(document)
        return document

    async def _index(
        self, db: Session, document: Document, suffix: str, provider: LLMProvider | None
    ) -> None:
        text = extract_text(Path(document.storage_path).read_bytes(), suffix)
        chunks = chunk_text(text, self._settings.CHUNK_SIZE, self._settings.CHUNK_OVERLAP)
        embeddings: list[list[float]] = []
        if provider is not None and chunks:
            try:
                embeddings = await provider.aembed(chunks)
            except ProviderError:
                embeddings = []

        for index, content in enumerate(chunks):
            db.add(
                DocumentChunk(
                    document_id=document.id,
                    user_id=document.user_id,
                    chunk_index=index,
                    content=content,
                    embedding_json=embeddings[index] if index < len(embeddings) else None,
                    token_count=len(content.split()),
                )
            )
        document.status = DOCUMENT_STATUS_READY
        document.chunk_count = len(chunks)
        db.commit()

    async def search(
        self,
        db: Session,
        user: User,
        query: str,
        limit: int,
        provider: LLMProvider | None = None,
    ) -> list[DocumentSearchResult]:
        chunks = list(
            db.scalars(
                select(DocumentChunk)
                .join(Document, DocumentChunk.document_id == Document.id)
                .where(
                    DocumentChunk.user_id == user.id,
                    Document.status == DOCUMENT_STATUS_READY,
                )
            )
        )
        if not chunks:
            return []

        query_vector: list[float] | None = None
        if provider is not None and any(chunk.embedding_json for chunk in chunks):
            try:
                query_vector = (await provider.aembed([query]))[0]
            except (ProviderError, IndexError):
                query_vector = None

        scored: list[tuple[float, DocumentChunk]] = []
        for chunk in chunks:
            if query_vector is not None and chunk.embedding_json:
                score = cosine_similarity(query_vector, chunk.embedding_json)
            else:
                score = keyword_score(query, chunk.content)
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda pair: pair[0], reverse=True)

        results: list[DocumentSearchResult] = []
        for score, chunk in scored[:limit]:
            document = db.get(Document, chunk.document_id)
            if document is None:
                continue
            results.append(
                DocumentSearchResult(
                    document_id=document.id,
                    filename=document.filename,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    score=round(score, 4),
                )
            )
        return results

    def delete(self, db: Session, document: Document) -> None:
        path = Path(document.storage_path)
        db.delete(document)
        db.commit()
        try:
            path.unlink(missing_ok=True)
        except OSError:
            logger.warning("Could not remove uploaded file %s", path)
