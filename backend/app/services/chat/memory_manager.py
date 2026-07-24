"""
Conversation Memory Manager
============================
Manages conversation history with sliding window context management.
Ensures the LLM context window is never exceeded.
"""
from __future__ import annotations
import structlog
from typing import Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.chat import ConversationSession, ChatMessage

logger = structlog.get_logger(__name__)


class MemoryManager:
    """
    Loads, stores, and manages conversation history for a session.
    Implements sliding window to avoid context overflow.
    """

    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns

    async def get_history(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
    ) -> list[dict]:
        """
        Load conversation history as OpenAI-compatible message dicts.
        Only loads the last max_turns * 2 messages.
        """
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        messages = list(result.scalars().all())

        # Sliding window — keep only last N turns
        max_msgs = self.max_turns * 2
        if len(messages) > max_msgs:
            messages = messages[-max_msgs:]

        history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        logger.debug("memory_loaded", session_id=str(session_id), messages=len(history))
        return history

    async def save_user_message(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        content: str,
    ) -> ChatMessage:
        """Persist a user message."""
        msg = ChatMessage(
            session_id=session_id,
            role="user",
            content=content,
            token_count=self._estimate_tokens(content),
        )
        db.add(msg)
        await db.flush()  # Get ID without full commit
        return msg

    async def save_assistant_message(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        content: str,
        model_used: str | None = None,
        latency_ms: float | None = None,
        has_citations: bool = False,
    ) -> ChatMessage:
        """Persist an assistant message."""
        msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=content,
            token_count=self._estimate_tokens(content),
            model_used=model_used,
            latency_ms=latency_ms,
            has_citations=has_citations,
        )
        db.add(msg)
        await db.flush()
        return msg

    async def increment_session_stats(
        self,
        db: AsyncSession,
        session: ConversationSession,
        tokens: int = 0,
    ) -> None:
        """Update session-level counters."""
        session.total_messages += 2   # user + assistant
        session.total_tokens_used += tokens
        await db.flush()

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Rough token estimate: ~4 chars per token."""
        return max(1, len(text) // 4)
