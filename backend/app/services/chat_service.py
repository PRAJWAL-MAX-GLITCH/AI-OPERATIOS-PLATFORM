"""
Chat Service Facade
====================
Top-level service that delegates to the ChatOrchestrator and SessionManager.
This is the primary entry point for all chat operations.
"""
from __future__ import annotations
import uuid
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.chat.orchestrator import chat_orchestrator
from app.services.chat.session_manager import SessionManager
from app.models.chat import ConversationSession, ChatMessage, ChatCitation

_session_mgr = SessionManager()


class ChatService:
    """Facade over the chat subsystem. Used by the API layer."""

    # ------------------------------------------------------------------
    # Chat Operations
    # ------------------------------------------------------------------

    async def chat(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        knowledge_base_id: uuid.UUID,
        question: str,
        session_id: uuid.UUID | None = None,
    ) -> dict:
        """Non-streaming Q&A."""
        return await chat_orchestrator.chat(
            db=db,
            user_id=user_id,
            knowledge_base_id=knowledge_base_id,
            question=question,
            session_id=session_id,
        )

    async def chat_stream(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        knowledge_base_id: uuid.UUID,
        question: str,
        session_id: uuid.UUID | None = None,
    ) -> AsyncIterator[str]:
        """Streaming Q&A via SSE."""
        async for chunk in chat_orchestrator.chat_stream(
            db=db,
            user_id=user_id,
            knowledge_base_id=knowledge_base_id,
            question=question,
            session_id=session_id,
        ):
            yield chunk

    # ------------------------------------------------------------------
    # Session Operations
    # ------------------------------------------------------------------

    async def list_sessions(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 20,
    ) -> list[ConversationSession]:
        return await _session_mgr.list_sessions(db, user_id, limit=limit)

    async def get_session(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ConversationSession | None:
        return await _session_mgr.get_session(db, session_id, user_id)

    async def delete_session(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        return await _session_mgr.delete_session(db, session_id, user_id)

    async def get_session_citations(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[ChatCitation]:
        return await _session_mgr.get_session_citations(db, session_id, user_id)

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    async def cleanup_expired_sessions(self, db: AsyncSession) -> int:
        return await _session_mgr.cleanup_expired_sessions(db)


chat_service = ChatService()
