"""
FAISS Vector Store — Abstraction Layer
=======================================
All FAISS operations go through this class.
Future backends (ChromaDB, Pinecone, Weaviate) only need to implement
the same interface and register in VectorStoreFactory.
"""
from __future__ import annotations
import json
import numpy as np
import faiss
import structlog
from pathlib import Path
from typing import Optional

logger = structlog.get_logger(__name__)


class FAISSVectorStore:
    """
    Production FAISS index with metadata mapping.
    Uses IndexFlatIP (inner product) for normalized vectors = cosine similarity.
    """

    def __init__(self, vector_dim: int, index_path: str):
        self.vector_dim = vector_dim
        self.index_path = Path(index_path)
        self.meta_path  = self.index_path.with_suffix(".meta.json")
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        # id_map[faiss_int] = chunk_id (str UUID)
        self._id_map: list[str] = []
        self._index: Optional[faiss.IndexFlatIP] = None

    # ------------------------------------------------------------------
    # Index lifecycle
    # ------------------------------------------------------------------

    def _get_or_create_index(self) -> faiss.IndexFlatIP:
        if self._index is None:
            self._index = faiss.IndexFlatIP(self.vector_dim)
        return self._index

    def add(self, vectors: np.ndarray, chunk_ids: list[str]) -> None:
        """Add normalized vectors to the FAISS index."""
        assert vectors.shape[0] == len(chunk_ids), "vectors and chunk_ids must have same length"
        index = self._get_or_create_index()
        faiss.normalize_L2(vectors)
        index.add(vectors)
        self._id_map.extend(chunk_ids)
        logger.info("faiss_vectors_added", n=len(chunk_ids), total=index.ntotal)

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> list[tuple[str, float]]:
        """
        Searches the index for top_k nearest neighbors.
        Returns list of (chunk_id, similarity_score) sorted descending.
        """
        index = self._get_or_create_index()
        if index.ntotal == 0:
            return []

        q = query_vector.reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(q)
        scores, idxs = index.search(q, min(top_k, index.ntotal))

        results = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx >= 0 and idx < len(self._id_map):
                results.append((self._id_map[idx], float(score)))
        return results

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Persist the FAISS index and id mapping to disk."""
        if self._index is None:
            return
        faiss.write_index(self._index, str(self.index_path))
        self.meta_path.write_text(json.dumps({"id_map": self._id_map, "dim": self.vector_dim}))
        logger.info("faiss_index_saved", path=str(self.index_path), vectors=self._index.ntotal)

    def load(self) -> bool:
        """Load a persisted index from disk. Returns True if successful."""
        if not self.index_path.exists():
            return False
        self._index = faiss.read_index(str(self.index_path))
        meta = json.loads(self.meta_path.read_text())
        self._id_map = meta["id_map"]
        logger.info("faiss_index_loaded", path=str(self.index_path), vectors=self._index.ntotal)
        return True

    def clear(self) -> None:
        """Reset the index in memory and remove from disk."""
        self._index  = faiss.IndexFlatIP(self.vector_dim)
        self._id_map = []
        if self.index_path.exists():
            self.index_path.unlink()
        if self.meta_path.exists():
            self.meta_path.unlink()
        logger.info("faiss_index_cleared")

    @property
    def total_vectors(self) -> int:
        if self._index is None:
            return 0
        return self._index.ntotal


# ---------------------------------------------------------------------------
# Factory — future backends register here
# ---------------------------------------------------------------------------

class VectorStoreFactory:
    _REGISTRY = {"faiss": FAISSVectorStore}

    @classmethod
    def register(cls, name: str, store_class: type) -> None:
        cls._REGISTRY[name] = store_class

    @classmethod
    def create(cls, backend: str, vector_dim: int, index_path: str, **kwargs) -> FAISSVectorStore:
        cls_ = cls._REGISTRY.get(backend)
        if not cls_:
            raise ValueError(f"Unknown vector store backend '{backend}'.")
        return cls_(vector_dim, index_path, **kwargs)
