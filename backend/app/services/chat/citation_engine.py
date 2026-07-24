"""
Citation Engine
===============
Extracts, ranks, and formats source citations from RAG retrieval results.
Every AI response MUST include citations. No citation = no answer.

Citation confidence levels:
  high   — similarity ≥ 0.80
  medium — similarity ≥ 0.60
  low    — similarity < 0.60
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import uuid
import structlog

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chat import ChatCitation

logger = structlog.get_logger(__name__)


@dataclass
class CitationData:
    """Structured citation data for a single source chunk."""
    chunk_id:         str
    source_document:  str
    page_number:      Optional[int]
    excerpt:          str
    similarity_score: float
    confidence:       str   # high | medium | low

    def to_dict(self) -> dict:
        return {
            "chunk_id":         self.chunk_id,
            "source_document":  self.source_document,
            "page_number":      self.page_number,
            "excerpt":          self.excerpt[:300] + "..." if len(self.excerpt) > 300 else self.excerpt,
            "similarity_score": round(self.similarity_score, 4),
            "confidence":       self.confidence,
        }


class CitationEngine:
    """
    Transforms raw RAG retrieval results into structured, ranked citations.
    """

    HIGH_CONFIDENCE_THRESHOLD   = 0.80
    MEDIUM_CONFIDENCE_THRESHOLD = 0.60
    MAX_CITATIONS               = 5
    EXCERPT_MAX_CHARS           = 500

    def build_citations(
        self,
        retrieval_results: list[dict],
    ) -> list[CitationData]:
        """
        Build structured citations from retrieval results.
        Input format: [{"chunk_id": str, "text": str, "score": float, "source": str, "page": int|None}]
        """
        if not retrieval_results:
            logger.warning("citation_engine_no_results")
            return []

        citations: list[CitationData] = []
        seen_sources: set[str] = set()

        # Sort by score descending
        sorted_results = sorted(retrieval_results, key=lambda x: x.get("score", 0), reverse=True)

        for result in sorted_results[:self.MAX_CITATIONS]:
            score       = float(result.get("score", 0))
            source      = result.get("source", "unknown_document")
            text        = result.get("text", "").strip()
            chunk_id    = result.get("chunk_id", str(uuid.uuid4()))
            page        = result.get("page")

            confidence = self._score_to_confidence(score)
            excerpt    = text[:self.EXCERPT_MAX_CHARS]

            citation = CitationData(
                chunk_id=chunk_id,
                source_document=self._clean_source_name(source),
                page_number=page,
                excerpt=excerpt,
                similarity_score=score,
                confidence=confidence,
            )
            citations.append(citation)

        logger.info("citations_built", count=len(citations), top_score=citations[0].similarity_score if citations else 0)
        return citations

    async def persist_citations(
        self,
        db: AsyncSession,
        message_id: uuid.UUID,
        citations: list[CitationData],
    ) -> list[ChatCitation]:
        """Save citation records to the database."""
        db_citations = []
        for c in citations:
            record = ChatCitation(
                message_id=message_id,
                chunk_id=c.chunk_id,
                source_document=c.source_document,
                page_number=c.page_number,
                excerpt=c.excerpt,
                similarity_score=c.similarity_score,
                confidence=c.confidence,
            )
            db.add(record)
            db_citations.append(record)

        await db.flush()
        logger.info("citations_persisted", message_id=str(message_id), count=len(db_citations))
        return db_citations

    def format_for_response(self, citations: list[CitationData]) -> list[dict]:
        """Convert citations to API response format."""
        return [c.to_dict() for c in citations]

    def build_context_with_citations(
        self,
        citations: list[CitationData],
        max_chars: int = 6000,
    ) -> str:
        """Build context string from citations for the prompt."""
        parts:  list[str] = []
        total_chars = 0

        for i, c in enumerate(citations, 1):
            header = f"[Source {i}: {c.source_document}" + (f", Page {c.page_number}" if c.page_number else "") + "]"
            section = f"{header}\n{c.excerpt}"
            if total_chars + len(section) > max_chars:
                break
            parts.append(section)
            total_chars += len(section)

        return "\n\n---\n\n".join(parts)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _score_to_confidence(self, score: float) -> str:
        if score >= self.HIGH_CONFIDENCE_THRESHOLD:
            return "high"
        elif score >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            return "medium"
        return "low"

    def _clean_source_name(self, source: str) -> str:
        """Extract a clean document name from a file path."""
        if not source:
            return "Unknown Document"
        # Handle both / and \ path separators
        parts = source.replace("\\", "/").split("/")
        return parts[-1] if parts else source
