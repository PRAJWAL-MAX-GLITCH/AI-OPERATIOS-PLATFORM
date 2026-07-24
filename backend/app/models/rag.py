"""
RAG Domain Models
=================
Entities for the Enterprise RAG system.
KnowledgeBase → Document → Chunk → Embedding → Index
"""
from __future__ import annotations
from sqlalchemy import String, ForeignKey, Integer, Float, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON
from typing import Optional, Any
from app.models.base import UUIDBaseModel
import uuid


class KnowledgeBase(UUIDBaseModel):
    """Logical container that groups related documents."""
    __tablename__ = "rag_knowledge_bases"

    name:          Mapped[str]           = mapped_column(String(255), nullable=False, unique=True)
    description:   Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding_model: Mapped[str]         = mapped_column(String(255), default="all-MiniLM-L6-v2")
    chunk_size:    Mapped[int]           = mapped_column(Integer, default=512)
    chunk_overlap: Mapped[int]           = mapped_column(Integer, default=64)
    is_indexed:    Mapped[bool]          = mapped_column(Boolean, default=False)
    index_path:    Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    total_documents: Mapped[int]         = mapped_column(Integer, default=0)
    total_chunks:  Mapped[int]           = mapped_column(Integer, default=0)
    metadata_:     Mapped[Optional[dict[str, Any]]] = mapped_column("metadata", JSON().with_variant(JSONB, 'postgresql'), nullable=True)

    documents: Mapped[list["RAGDocument"]] = relationship("RAGDocument", back_populates="knowledge_base", cascade="all, delete-orphan")


class RAGDocument(UUIDBaseModel):
    """Individual document ingested into a knowledge base."""
    __tablename__ = "rag_documents"

    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rag_knowledge_bases.id"), nullable=False, index=True)
    filename:    Mapped[str]           = mapped_column(String(512), nullable=False)
    file_path:   Mapped[str]           = mapped_column(String(1024), nullable=False)
    file_type:   Mapped[str]           = mapped_column(String(50),  nullable=False)  # pdf|docx|txt|md|html
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status:      Mapped[str]           = mapped_column(String(50), default="pending")  # pending|processing|indexed|failed
    error_msg:   Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_chunks: Mapped[int]          = mapped_column(Integer, default=0)
    doc_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)

    knowledge_base: Mapped["KnowledgeBase"] = relationship("KnowledgeBase", back_populates="documents")
    chunks: Mapped[list["RAGChunk"]]        = relationship("RAGChunk", back_populates="document", cascade="all, delete-orphan")


class RAGChunk(UUIDBaseModel):
    """A text chunk extracted from a RAGDocument."""
    __tablename__ = "rag_chunks"

    document_id:   Mapped[uuid.UUID] = mapped_column(ForeignKey("rag_documents.id"), nullable=False, index=True)
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rag_knowledge_bases.id"), nullable=False, index=True)
    chunk_index:   Mapped[int]       = mapped_column(Integer, nullable=False)
    text:          Mapped[str]       = mapped_column(Text, nullable=False)
    char_count:    Mapped[int]       = mapped_column(Integer, default=0)
    token_estimate: Mapped[int]      = mapped_column(Integer, default=0)
    page_number:   Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    chunk_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)

    document: Mapped["RAGDocument"] = relationship("RAGDocument", back_populates="chunks")


class RAGIndex(UUIDBaseModel):
    """FAISS index metadata for a knowledge base."""
    __tablename__ = "rag_indexes"

    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rag_knowledge_bases.id"), nullable=False, unique=True)
    index_path:   Mapped[str]           = mapped_column(String(1024), nullable=False)
    index_type:   Mapped[str]           = mapped_column(String(50),   default="IndexFlatL2")
    embedding_model: Mapped[str]        = mapped_column(String(255),  nullable=False)
    vector_dim:   Mapped[int]           = mapped_column(Integer,      nullable=False)
    total_vectors: Mapped[int]          = mapped_column(Integer,      default=0)
    build_config: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)


class RetrievalLog(UUIDBaseModel):
    """Audit log for every search/retrieval operation."""
    __tablename__ = "rag_retrieval_logs"

    knowledge_base_id: Mapped[uuid.UUID]  = mapped_column(ForeignKey("rag_knowledge_bases.id"), nullable=False, index=True)
    query:        Mapped[str]            = mapped_column(Text, nullable=False)
    top_k:        Mapped[int]            = mapped_column(Integer, default=5)
    results_count: Mapped[int]           = mapped_column(Integer, default=0)
    latency_ms:   Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    retrieved_chunk_ids: Mapped[Optional[list]] = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
