"""
Chat Domain Models
==================
Entities for the Enterprise RAG Chat System.
ConversationSession → ChatMessage → ChatCitation
"""
from __future__ import annotations
from sqlalchemy import String, ForeignKey, Integer, Float, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON
from typing import Optional, Any
from app.models.base import UUIDBaseModel
import uuid


class ConversationSession(UUIDBaseModel):
    """A single conversation session between a user and the RAG assistant."""
    __tablename__ = "conversation_sessions"

    user_id:           Mapped[uuid.UUID]      = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    knowledge_base_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("rag_knowledge_bases.id"), nullable=True, index=True)
    title:             Mapped[str]            = mapped_column(String(255), nullable=False, default="New Conversation")
    llm_provider:      Mapped[str]            = mapped_column(String(50), nullable=False, default="ollama")
    llm_model:         Mapped[str]            = mapped_column(String(100), nullable=False, default="llama3")
    total_turns:       Mapped[int]            = mapped_column(Integer, default=0)
    last_activity_at:  Mapped[Optional[str]]  = mapped_column(String(50), nullable=True)

    messages:  Mapped[list["ChatMessage"]]   = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")
    audit_logs: Mapped[list["ChatAuditLog"]] = relationship("ChatAuditLog", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(UUIDBaseModel):
    """A single message in a conversation session (user or assistant)."""
    __tablename__ = "chat_messages"

    session_id:   Mapped[uuid.UUID]           = mapped_column(ForeignKey("conversation_sessions.id"), nullable=False, index=True)
    role:         Mapped[str]                 = mapped_column(String(20), nullable=False)  # user | assistant | system
    content:      Mapped[str]                 = mapped_column(Text, nullable=False)
    token_count:  Mapped[Optional[int]]       = mapped_column(Integer, nullable=True)
    latency_ms:   Mapped[Optional[float]]     = mapped_column(Float, nullable=True)
    model_used:   Mapped[Optional[str]]       = mapped_column(String(100), nullable=True)
    finish_reason: Mapped[Optional[str]]      = mapped_column(String(50), nullable=True)
    extra_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column("extra_metadata", JSON().with_variant(JSONB, 'postgresql'), nullable=True)

    session:   Mapped["ConversationSession"] = relationship("ConversationSession", back_populates="messages")
    citations: Mapped[list["ChatCitation"]]  = relationship("ChatCitation", back_populates="message", cascade="all, delete-orphan")


class ChatCitation(UUIDBaseModel):
    """A source citation linked to an assistant message."""
    __tablename__ = "chat_citations"

    message_id:        Mapped[uuid.UUID]       = mapped_column(ForeignKey("chat_messages.id"), nullable=False, index=True)
    chunk_id:          Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("rag_chunks.id"), nullable=True)
    document_id:       Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("rag_documents.id"), nullable=True)
    citation_text:     Mapped[str]             = mapped_column(Text, nullable=False)
    source_filename:   Mapped[Optional[str]]   = mapped_column(String(512), nullable=True)
    relevance_score:   Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    chunk_index:       Mapped[Optional[int]]   = mapped_column(Integer, nullable=True)

    message: Mapped["ChatMessage"] = relationship("ChatMessage", back_populates="citations")


class ChatAuditLog(UUIDBaseModel):
    """Immutable audit trail for all chat events."""
    __tablename__ = "chat_audit_logs"

    session_id:  Mapped[uuid.UUID]            = mapped_column(ForeignKey("conversation_sessions.id"), nullable=False, index=True)
    user_id:     Mapped[uuid.UUID]            = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    event_type:  Mapped[str]                  = mapped_column(String(100), nullable=False)
    event_data:  Mapped[Optional[dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    severity:    Mapped[str]                  = mapped_column(String(20), nullable=False, default="info")

    session: Mapped["ConversationSession"] = relationship("ConversationSession", back_populates="audit_logs")
