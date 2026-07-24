"""
Agent State and Context
=======================
Manages the runtime state, execution context, and tracking for an agent's ReAct loop.
"""
from __future__ import annotations
import uuid
from typing import Any, List, Optional
from datetime import datetime, timezone
import structlog
from app.models.agent import AgentRun, AgentTask

logger = structlog.get_logger(__name__)


class AgentState:
    """
    Mutable state passed through the agent execution loop.
    Contains counters, memory buffers, and early termination signals.
    """
    def __init__(self, max_steps: int = 15):
        self.current_step: int = 0
        self.max_steps: int = max_steps
        self.is_finished: bool = False
        self.final_answer: Optional[str] = None
        self.error: Optional[str] = None
        self.scratchpad: List[dict] = []  # Temporary memory for the current run (observations, intermediate steps)
        
    def increment_step(self):
        self.current_step += 1
        if self.current_step >= self.max_steps:
            self.error = f"Agent exceeded maximum allowed steps ({self.max_steps})."
            self.is_finished = True
            logger.warning("agent_max_steps_exceeded", max_steps=self.max_steps)

    def add_observation(self, tool_name: str, args: dict, result: str):
        """Add a tool execution observation to the scratchpad."""
        self.scratchpad.append({
            "type": "tool_execution",
            "tool": tool_name,
            "args": args,
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })


class AgentContext:
    """
    Immutable or environment context provided to the agent.
    Includes DB session pointers (abstracted), Task details, and User info.
    """
    def __init__(
        self, 
        task_id: uuid.UUID,
        run_id: uuid.UUID,
        user_id: uuid.UUID,
        project_id: Optional[uuid.UUID] = None,
        task_title: str = "",
        task_description: str = "",
        db_session: Any = None  # AsyncSession
    ):
        self.task_id = task_id
        self.run_id = run_id
        self.user_id = user_id
        self.project_id = project_id
        self.task_title = task_title
        self.task_description = task_description
        self.db = db_session
