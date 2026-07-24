"""
Conversation Session Manager
=============================
CRUD operations for conversation sessions.
Handles session lifecycle, auto-expiration, and cleanup.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.chat import ConversationSession, ChatMessage, ChatCitation, ChatAuditLog
from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class SessionManager:
    """Manages conversation session lifecycle."""

    async def create_session(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        knowledge_base_id: uuid.UUID | None = None,
        title: str | None = None,
        llm_provider: str | None = None,
        llm_model: str | None = None,
    ) -> ConversationSession:
        """Create a new conversation session."""
        session = ConversationSession(
            user_id=user_id,
            knowledge_base_id=knowledge_base_id,
            title=title or "New Conversation",
            llm_provider=llm_provider or settings.LLM_PROVIDER,
            llm_model=llm_model or settings.OLLAMA_MODEL,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        logger.info("session_created", session_id=str(session.id), user_id=str(user_id))
        return session

    async def get_session(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ConversationSession | None:
        """Get a session, ensuring it belongs to the user."""
        result = await db.execute(
            select(ConversationSession).where(
                ConversationSession.id == session_id,
                ConversationSession.user_id == user_id,
                ConversationSession.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def list_sessions(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 20,
    ) -> list[ConversationSession]:
        """List all active sessions for a user, newest first."""
        result = await db.execute(
            select(ConversationSession)
            .where(
                ConversationSession.user_id == user_id,
                ConversationSession.is_active == True,
            )
            .order_by(ConversationSession.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def delete_session(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """Soft-delete a session (marks is_active=False)."""
        session = await self.get_session(db, session_id, user_id)
        if not session:
            return False
        session.is_active = False
        await db.commit()
        logger.info("session_deleted", session_id=str(session_id))
        return True

    async def update_title_from_question(
        self,
        db: AsyncSession,
        session: ConversationSession,
        question: str,
    ) -> None:
        """Auto-generate a session title from the first question."""
        if session.title == "New Conversation":
            session.title = question[:80] + ("..." if len(question) > 80 else "")
            await db.flush()

    async def log_audit_event(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        event_type: str,
        event_data: dict | None = None,
        severity: str = "info",
    ) -> None:
        """Write an immutable audit log entry."""
        entry = ChatAuditLog(
            session_id=session_id,
            user_id=user_id,
            event_type=event_type,
            event_data=event_data or {},
            severity=severity,
        )
        db.add(entry)
        await db.flush()

    async def get_session_citations(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[ChatCitation]:
        """Get all citations for a session's messages."""
        # Verify session ownership
        session = await self.get_session(db, session_id, user_id)
        if not session:
            return []

        result = await db.execute(
            select(ChatCitation)
            .join(ChatMessage, ChatCitation.message_id == ChatMessage.id)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatCitation.created_at.desc())
        )
        return list(result.scalars().all())

    async def cleanup_expired_sessions(self, db: AsyncSession) -> int:
        """Background task: soft-delete sessions older than TTL."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.CHAT_SESSION_TTL_HOURS)
        result = await db.execute(
            select(ConversationSession).where(
                ConversationSession.created_at < cutoff,
                ConversationSession.is_active == True,
            )
        )
        sessions = list(result.scalars().all())
        count = 0
        for session in sessions:
            session.is_active = False
            count += 1
        if count:
            await db.commit()
            logger.info("sessions_expired", count=count)
        return count
