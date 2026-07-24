"""
Agent Communicator
==================
Handles message passing between agents.
"""
from __future__ import annotations
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.agents.memory.manager import AgentMemoryManager


class AgentCommunicator:
    """Message passing framework for multi-agent collaboration."""

    @staticmethod
    async def send_message(
        db: AsyncSession, 
        task_id: uuid.UUID, 
        sender: str, 
        receiver: str, 
        content: str
    ):
        """Send a message from one agent to another."""
        return await AgentMemoryManager.save_message(
            db=db,
            task_id=task_id,
            sender=sender,
            role="assistant",  # The sender is acting as an assistant in this context
            content=content,
            receiver=receiver
        )

    @staticmethod
    async def broadcast(
        db: AsyncSession,
        task_id: uuid.UUID,
        sender: str,
        content: str
    ):
        """Broadcast a message to all agents on the task."""
        return await AgentMemoryManager.save_message(
            db=db,
            task_id=task_id,
            sender=sender,
            role="assistant",
            content=content,
            receiver="*"
        )
