"""
Embedding Engine
================
Wraps Sentence-Transformers to generate dense vector embeddings.
Model is swappable via config — no downstream code changes needed.
"""
from __future__ import annotations
import numpy as np
import structlog
from functools import lru_cache
from typing import Optional

logger = structlog.get_logger(__name__)

DEFAULT_MODEL = "all-MiniLM-L6-v2"


@lru_cache(maxsize=3)
def _load_model(model_name: str):
    """Lazily loads and caches a SentenceTransformer model."""
    from sentence_transformers import SentenceTransformer
    logger.info("embedding_model_loading", model=model_name)
    return SentenceTransformer(model_name)


class EmbeddingEngine:
    """
    Wraps SentenceTransformer for batch text embedding.
    Swappable by changing model_name — interface stays identical.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self._model     = None

    @property
    def model(self):
        if self._model is None:
            self._model = _load_model(self.model_name)
        return self._model

    @property
    def vector_dim(self) -> int:
        return self.model.get_sentence_embedding_dimension()

    def embed(self, texts: list[str], batch_size: int = 64, show_progress: bool = False) -> np.ndarray:
        """
        Embeds a list of text strings.
        Returns np.ndarray of shape (n, embedding_dim), dtype float32.
        """
        if not texts:
            return np.empty((0, self.vector_dim), dtype=np.float32)

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True,
            normalize_embeddings=True,  # L2-normalize for cosine similarity via dot-product
        )
        logger.info("embeddings_generated", n=len(texts), dim=embeddings.shape[1])
        return embeddings.astype(np.float32)

    def embed_single(self, text: str) -> np.ndarray:
        """Embeds a single query string. Returns shape (dim,)."""
        return self.embed([text])[0]
