import hashlib
import re
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import MEMORY_KIND_FACT
from app.core.errors import AppError
from app.llm.base import LLMProvider
from app.llm.errors import ProviderError
from app.models import Memory, User
from app.utils.vector import cosine_similarity, keyword_score

_SENSITIVE_PATTERN = re.compile(
    r"(api[_-]?key|secret|password|passwd|token|private[_-]?key|credit[_-]?card|"
    r"ssn|social[_-]?security)",
    re.IGNORECASE,
)

_EXTRACTION_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bmy name is\s+(.+?)[.!?]?$", re.IGNORECASE), MEMORY_KIND_FACT),
    (re.compile(r"\bi (?:prefer|like|enjoy)\s+(.+?)[.!?]?$", re.IGNORECASE), "preference"),
    (re.compile(r"\bi(?:'m| am) (?:working on|building)\s+(.+?)[.!?]?$", re.IGNORECASE), "project"),
    (re.compile(r"\bi (?:use|usually use|work with)\s+(.+?)[.!?]?$", re.IGNORECASE), "preference"),
    (re.compile(r"\bi(?:'m| am) learning\s+(.+?)[.!?]?$", re.IGNORECASE), "fact"),
    (re.compile(r"\bplease always\s+(.+?)[.!?]?$", re.IGNORECASE), "instruction"),
    (re.compile(r"\bremember that\s+(.+?)[.!?]?$", re.IGNORECASE), MEMORY_KIND_FACT),
)


class MemoryService:
    def list(
        self, db: Session, user: User, limit: int, offset: int
    ) -> tuple[list[Memory], int]:
        total = (
            db.scalar(select(func.count()).select_from(Memory).where(Memory.user_id == user.id))
            or 0
        )
        items = list(
            db.scalars(
                select(Memory)
                .where(Memory.user_id == user.id)
                .order_by(Memory.created_at.desc(), Memory.id.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        return items, total

    def get(self, db: Session, user: User, memory_id) -> Memory:
        memory = db.scalar(
            select(Memory).where(Memory.id == memory_id, Memory.user_id == user.id)
        )
        if memory is None:
            raise AppError("Memory not found.", status_code=404, error_code="not_found")
        return memory

    async def create(
        self,
        db: Session,
        user: User,
        *,
        content: str,
        kind: str = MEMORY_KIND_FACT,
        source: str | None = None,
        confidence: float = 0.8,
        provider: LLMProvider | None = None,
    ) -> Memory:
        normalized = " ".join(content.split())
        content_hash = self._hash(normalized)
        embedding = await self._embed(provider, normalized) if provider else None
        existing = db.scalar(
            select(Memory).where(
                Memory.user_id == user.id,
                Memory.kind == kind,
                Memory.content_hash == content_hash,
            )
        )
        if existing is not None:
            existing.content = normalized
            existing.source = source or existing.source
            existing.confidence = confidence
            if embedding is not None:
                existing.embedding_json = embedding
            db.commit()
            db.refresh(existing)
            return existing

        memory = Memory(
            user_id=user.id,
            content=normalized,
            content_hash=content_hash,
            kind=kind,
            source=source,
            confidence=confidence,
            embedding_json=embedding,
        )
        db.add(memory)
        db.commit()
        db.refresh(memory)
        return memory

    async def update(
        self,
        db: Session,
        memory: Memory,
        *,
        content: str,
        kind: str | None = None,
        provider: LLMProvider | None = None,
    ) -> Memory:
        normalized = " ".join(content.split())
        if normalized != memory.content:
            memory.content = normalized
            memory.content_hash = self._hash(normalized)
            if provider is not None:
                memory.embedding_json = await self._embed(provider, normalized)
        if kind is not None:
            memory.kind = kind
        db.commit()
        db.refresh(memory)
        return memory

    def delete(self, db: Session, memory: Memory) -> None:
        db.delete(memory)
        db.commit()

    async def retrieve(
        self,
        db: Session,
        user: User,
        query: str,
        top_k: int,
        provider: LLMProvider | None = None,
    ) -> list[Memory]:
        memories = list(
            db.scalars(
                select(Memory)
                .where(Memory.user_id == user.id)
                .order_by(Memory.created_at.desc())
                .limit(200)
            )
        )
        if not memories:
            return []
        if not query.strip():
            return memories[:top_k]

        if provider is not None and any(item.embedding_json for item in memories):
            query_vector = await self._embed(provider, query)
            if query_vector:
                scored = [
                    (
                        cosine_similarity(query_vector, item.embedding_json)
                        if item.embedding_json
                        else 0.0,
                        item,
                    )
                    for item in memories
                ]
                scored.sort(key=lambda pair: pair[0], reverse=True)
                return [item for score, item in scored[:top_k] if score > 0]

        scored = [(keyword_score(query, item.content), item) for item in memories]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for score, item in scored[:top_k] if score > 0]

    async def extract_from_text(
        self,
        db: Session,
        user: User,
        text: str,
        *,
        source: str = "conversation",
        provider: LLMProvider | None = None,
    ) -> list[Memory]:
        extracted: list[Memory] = []
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
            candidate = sentence.strip()
            if not candidate or len(candidate) > 400:
                continue
            for pattern, kind in _EXTRACTION_RULES:
                match = pattern.search(candidate)
                if not match:
                    continue
                value = match.group(1).strip().strip("\"'")
                if not value or self._is_sensitive(value):
                    continue
                memory = await self.create(
                    db,
                    user,
                    content=candidate,
                    kind=kind,
                    source=source,
                    confidence=0.9,
                    provider=provider,
                )
                extracted.append(memory)
                break
        return extracted

    @staticmethod
    async def _embed(provider: LLMProvider, text: str) -> list[float] | None:
        try:
            vectors = await provider.aembed([text])
            return vectors[0] if vectors else None
        except ProviderError:
            return None

    @staticmethod
    def _hash(content: str) -> str:
        return hashlib.sha256(content.lower().encode("utf-8")).hexdigest()

    @staticmethod
    def _is_sensitive(text: str) -> bool:
        return bool(_SENSITIVE_PATTERN.search(text))
