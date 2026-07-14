"""
Retrieval Engine
================
Semantic search and context builder over the FAISS index.
"""
from __future__ import annotations
import time
import numpy as np
import structlog
from typing import Optional

from app.services.rag.embedder import EmbeddingEngine
from app.services.rag.vector_store import FAISSVectorStore

logger = structlog.get_logger(__name__)


class RetrievalEngine:

    def __init__(self, embedder: EmbeddingEngine, store: FAISSVectorStore):
        self.embedder = embedder
        self.store    = store

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[tuple[str, float]]:
        """
        Embeds the query and runs semantic similarity search.
        Returns list of (chunk_id, score).
        """
        t0 = time.perf_counter()
        q_vec = self.embedder.embed_single(query)
        results = self.store.search(q_vec, top_k=top_k)
        elapsed = (time.perf_counter() - t0) * 1000
        logger.info("retrieval_executed", query_len=len(query), top_k=top_k, results=len(results), latency_ms=round(elapsed, 2))
        return results


class ContextBuilder:
    """
    Merges retrieved chunk texts into a coherent context string,
    maintaining document order and deduplicating identical chunks.
    """

    def __init__(self, max_context_chars: int = 4000):
        self.max_context_chars = max_context_chars

    def build(
        self,
        chunks: list[dict],  # [{"chunk_id": str, "text": str, "score": float, "source": str}]
    ) -> str:
        """
        Deduplicates and concatenates retrieved chunks up to max_context_chars.
        """
        seen, parts, total = set(), [], 0

        # Sort by score descending to keep most relevant first
        sorted_chunks = sorted(chunks, key=lambda x: x.get("score", 0), reverse=True)

        for chunk in sorted_chunks:
            text = chunk.get("text", "").strip()
            if not text or text in seen:
                continue
            if total + len(text) > self.max_context_chars:
                break
            seen.add(text)
            source = chunk.get("source", "Unknown")
            parts.append(f"[Source: {source}]\n{text}")
            total += len(text)

        return "\n\n---\n\n".join(parts)
