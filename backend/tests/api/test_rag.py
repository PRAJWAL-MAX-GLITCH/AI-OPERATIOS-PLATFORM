"""
RAG Infrastructure Tests
=========================
Tests for loaders, cleaner, chunker, embedder, vector store, retriever.
Does NOT require any PDFs to exist. Uses in-memory text fixtures.
"""
import pytest
import numpy as np
import uuid
import tempfile
import os
from pathlib import Path

from app.services.rag.cleaner import clean_text
from app.services.rag.chunker import ChunkingEngine, Chunk
from app.services.rag.embedder import EmbeddingEngine
from app.services.rag.vector_store import FAISSVectorStore
from app.services.rag.retriever import RetrievalEngine, ContextBuilder
from app.services.rag.loaders import TxtLoader, MarkdownLoader, HtmlLoader, supported_extensions


# ===========================================================================
# Sample Text Fixture
# ===========================================================================

SAMPLE_TEXT = """
Retrieval-Augmented Generation (RAG) is an AI framework that combines retrieval systems
with generative language models to produce accurate, grounded responses.

The system retrieves relevant chunks from a knowledge base and provides them as context
to a language model. This approach significantly reduces hallucination.

Embeddings are dense vector representations of text. Sentence Transformers produce
high-quality embeddings by training on sentence-level semantic similarity tasks.

FAISS (Facebook AI Similarity Search) is a library for efficient similarity search
over large collections of dense vectors. It supports both CPU and GPU acceleration.

The RAG pipeline consists of: Document Loading → Cleaning → Chunking → Embedding → Indexing → Retrieval.
"""


# ===========================================================================
# Cleaner Tests
# ===========================================================================

def test_clean_text_removes_extra_whitespace():
    noisy = "Hello    World\n\n\n\n\nEnd"
    result = clean_text(noisy)
    assert "    " not in result
    assert result.count("\n\n\n") == 0


def test_clean_text_handles_empty():
    assert clean_text("") == ""
    assert clean_text("   \n  ") == ""


def test_clean_text_normalizes_unicode():
    text = "caf\u00e9 na\u00efve"
    result = clean_text(text)
    assert len(result) > 0


def test_clean_text_removes_control_chars():
    text = "Hello\x00World\x07End"
    result = clean_text(text)
    assert "\x00" not in result
    assert "\x07" not in result


# ===========================================================================
# Chunker Tests
# ===========================================================================

def test_chunker_fixed_produces_chunks():
    engine = ChunkingEngine(chunk_size=100, chunk_overlap=20, strategy="fixed")
    chunks = engine.chunk(SAMPLE_TEXT)
    assert len(chunks) > 0
    assert all(isinstance(c, Chunk) for c in chunks)
    assert all(len(c.text) > 0 for c in chunks)


def test_chunker_recursive_produces_chunks():
    engine = ChunkingEngine(chunk_size=200, chunk_overlap=40, strategy="recursive")
    chunks = engine.chunk(SAMPLE_TEXT)
    assert len(chunks) > 0


def test_chunker_paragraph_produces_chunks():
    engine = ChunkingEngine(chunk_size=300, chunk_overlap=0, strategy="paragraph")
    chunks = engine.chunk(SAMPLE_TEXT)
    assert len(chunks) > 0


def test_chunker_sentence_produces_chunks():
    engine = ChunkingEngine(chunk_size=200, chunk_overlap=20, strategy="sentence")
    chunks = engine.chunk(SAMPLE_TEXT)
    assert len(chunks) > 0


def test_chunker_token_produces_chunks():
    engine = ChunkingEngine(chunk_size=50, chunk_overlap=10, strategy="token")
    chunks = engine.chunk(SAMPLE_TEXT)
    assert len(chunks) > 0


def test_chunk_has_token_estimate():
    engine = ChunkingEngine(chunk_size=100, chunk_overlap=0, strategy="fixed")
    chunks = engine.chunk("Hello world this is a test sentence.")
    for c in chunks:
        assert c.token_estimate > 0


def test_chunker_empty_text():
    engine = ChunkingEngine(chunk_size=100, chunk_overlap=20, strategy="fixed")
    chunks = engine.chunk("")
    assert chunks == []


# ===========================================================================
# Loaders Tests (no real files needed for txt/md/html)
# ===========================================================================

def test_txt_loader(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("Hello from a text file. This is RAG testing.", encoding="utf-8")
    loader = TxtLoader()
    text, meta = loader.load(str(f))
    assert "Hello" in text
    assert meta["file_type"] == "txt"


def test_markdown_loader(tmp_path):
    f = tmp_path / "test.md"
    f.write_text("# Title\n\nThis is **bold** text and [a link](http://example.com).", encoding="utf-8")
    loader = MarkdownLoader()
    text, meta = loader.load(str(f))
    assert "Title" in text
    assert "**" not in text   # Markdown stripped
    assert meta["file_type"] == "md"


def test_html_loader(tmp_path):
    f = tmp_path / "test.html"
    f.write_text("<html><head><title>RAG</title></head><body><p>Hello RAG world</p></body></html>", encoding="utf-8")
    loader = HtmlLoader()
    text, meta = loader.load(str(f))
    assert "Hello RAG world" in text
    assert meta["file_type"] == "html"


def test_supported_extensions():
    exts = supported_extensions()
    assert ".pdf"  in exts
    assert ".docx" in exts
    assert ".txt"  in exts
    assert ".md"   in exts
    assert ".html" in exts


# ===========================================================================
# Embedding Engine Tests
# ===========================================================================

def test_embedding_engine_shape():
    engine = EmbeddingEngine("all-MiniLM-L6-v2")
    texts  = ["Hello world", "Retrieval Augmented Generation"]
    vecs   = engine.embed(texts)
    assert vecs.shape == (2, engine.vector_dim)
    assert vecs.dtype == np.float32


def test_embedding_engine_single():
    engine = EmbeddingEngine("all-MiniLM-L6-v2")
    vec    = engine.embed_single("test sentence")
    assert len(vec.shape) == 1
    assert vec.shape[0] == engine.vector_dim


def test_embedding_engine_empty():
    engine = EmbeddingEngine("all-MiniLM-L6-v2")
    vecs   = engine.embed([])
    assert vecs.shape[0] == 0


def test_embedding_normalized():
    """Normalized embeddings should have L2 norm ≈ 1."""
    engine = EmbeddingEngine("all-MiniLM-L6-v2")
    vec    = engine.embed_single("check normalization")
    norm   = np.linalg.norm(vec)
    assert abs(norm - 1.0) < 0.01


# ===========================================================================
# FAISS Vector Store Tests
# ===========================================================================

def test_faiss_add_and_search(tmp_path):
    store = FAISSVectorStore(vector_dim=4, index_path=str(tmp_path / "test.index"))
    vecs  = np.random.randn(5, 4).astype(np.float32)
    ids   = [str(uuid.uuid4()) for _ in range(5)]
    store.add(vecs, ids)

    assert store.total_vectors == 5

    q_vec   = vecs[0]
    results = store.search(q_vec, top_k=3)
    assert len(results) == 3
    assert results[0][0] in ids


def test_faiss_save_and_load(tmp_path):
    store = FAISSVectorStore(vector_dim=4, index_path=str(tmp_path / "test.index"))
    vecs  = np.random.randn(3, 4).astype(np.float32)
    ids   = [str(uuid.uuid4()) for _ in range(3)]
    store.add(vecs, ids)
    store.save()

    store2 = FAISSVectorStore(vector_dim=4, index_path=str(tmp_path / "test.index"))
    loaded = store2.load()
    assert loaded
    assert store2.total_vectors == 3


def test_faiss_search_empty_index(tmp_path):
    store   = FAISSVectorStore(vector_dim=4, index_path=str(tmp_path / "empty.index"))
    q_vec   = np.random.randn(4).astype(np.float32)
    results = store.search(q_vec, top_k=5)
    assert results == []


def test_faiss_clear(tmp_path):
    store = FAISSVectorStore(vector_dim=4, index_path=str(tmp_path / "clear.index"))
    vecs  = np.random.randn(3, 4).astype(np.float32)
    store.add(vecs, [str(uuid.uuid4()) for _ in range(3)])
    store.save()
    store.clear()
    assert store.total_vectors == 0


# ===========================================================================
# Retriever Tests
# ===========================================================================

def test_retrieval_engine_end_to_end(tmp_path):
    """Full pipeline: embed texts → store in FAISS → retrieve with query."""
    embedder = EmbeddingEngine("all-MiniLM-L6-v2")
    store    = FAISSVectorStore(embedder.vector_dim, str(tmp_path / "retrieval.index"))

    texts = [
        "FAISS is a fast similarity search library.",
        "Sentence Transformers generate dense embeddings.",
        "RAG combines retrieval with generation.",
        "Python is a popular programming language.",
    ]
    vecs = embedder.embed(texts)
    ids  = [str(uuid.uuid4()) for _ in texts]
    store.add(vecs, ids)

    engine  = RetrievalEngine(embedder, store)
    results = engine.search("vector similarity search library", top_k=2)

    assert len(results) == 2
    # Top result should be semantically closest to FAISS
    top_id, top_score = results[0]
    assert top_id in ids
    assert 0.0 <= top_score <= 1.0 + 1e-5  # cosine similarity


# ===========================================================================
# Context Builder Tests
# ===========================================================================

def test_context_builder_deduplicates():
    chunks = [
        {"text": "Chunk A content", "score": 0.9, "source": "doc1.pdf"},
        {"text": "Chunk A content", "score": 0.8, "source": "doc1.pdf"},  # duplicate
        {"text": "Chunk B content", "score": 0.7, "source": "doc2.pdf"},
    ]
    builder = ContextBuilder(max_context_chars=2000)
    context = builder.build(chunks)
    # Should appear only once
    assert context.count("Chunk A content") == 1
    assert "Chunk B content" in context


def test_context_builder_respects_max_chars():
    chunks = [{"text": "A" * 500, "score": 0.9, "source": "doc.pdf"} for _ in range(20)]
    builder = ContextBuilder(max_context_chars=1000)
    context = builder.build(chunks)
    assert len(context) <= 1200  # some overhead from source annotations


def test_context_builder_empty():
    builder = ContextBuilder()
    context = builder.build([])
    assert context == ""
