"""
Agent Memory Manager
====================
Handles short-term and long-term memory for agent tasks.
Allows fetching conversation history, persisting messages, and context compression.
"""
from __future__ import annotations
import uuid
import structlog
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.agent import AgentMessage
from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class AgentMemoryManager:
    """
    Manages persistence and retrieval of agent task memory.
    """
    
    @staticmethod
    async def save_message(
        db: AsyncSession,
        task_id: uuid.UUID,
        sender: str,
        role: str,
        content: str,
        receiver: str | None = None,
        tool_calls: list | None = None,
        tool_call_id: str | None = None,
    ) -> AgentMessage:
        """
        Persist a single message to the shared task memory.
        """
        msg = AgentMessage(
            task_id=task_id,
            sender=sender,
            role=role,
            content=content,
            receiver=receiver,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            token_count=max(1, len(content) // 4)  # rough estimation
        )
        db.add(msg)
        await db.commit()
        return msg

    @staticmethod
    async def get_task_history(
        db: AsyncSession,
        task_id: uuid.UUID,
        limit: int = settings.AGENT_MAX_MEMORY_TURNS * 2
    ) -> List[Dict[str, Any]]:
        """
        Fetch the most recent messages for a task.
        Returns a list of OpenAI-compatible message dictionaries.
        """
        result = await db.execute(
            select(AgentMessage)
            .where(AgentMessage.task_id == task_id)
            .order_by(AgentMessage.created_at.asc())
        )
        messages = list(result.scalars().all())
        
        # Apply sliding window compression
        if len(messages) > limit:
            # We must be careful not to truncate in the middle of a tool call / response pair
            # For simplicity, we just take the last `limit` messages
            messages = messages[-limit:]
            logger.debug("memory_compressed", task_id=str(task_id), kept=limit)

        formatted_history = []
        for msg in messages:
            formatted = {
                "role": msg.role,
                "content": msg.content
            }
            if msg.tool_calls:
                formatted["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                formatted["tool_call_id"] = msg.tool_call_id
            if msg.sender:
                formatted["name"] = msg.sender.replace(":", "_").replace("-", "_")  # OpenAI names must be alphanumeric
                
            formatted_history.append(formatted)

        return formatted_history
