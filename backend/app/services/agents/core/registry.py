"""
Agent Registry and Factory
==========================
Dynamically registers and instantiates AI Agents based on their type string.
"""
from __future__ import annotations
from typing import Dict, Type
import structlog

from app.services.agents.core.base import BaseAgent

logger = structlog.get_logger(__name__)


class AgentRegistry:
    """Registry pattern for discovering and instantiating agents."""
    
    _REGISTRY: Dict[str, Type[BaseAgent]] = {}

    @classmethod
    def register(cls, agent_type: str):
        """Decorator to register an agent class."""
        def wrapper(agent_cls: Type[BaseAgent]):
            cls._REGISTRY[agent_type] = agent_cls
            logger.debug("agent_registered", agent_type=agent_type)
            return agent_cls
        return wrapper

    @classmethod
    def create(cls, agent_type: str, **kwargs) -> BaseAgent:
        """Instantiate an agent by its registered type."""
        agent_cls = cls._REGISTRY.get(agent_type)
        if not agent_cls:
            raise ValueError(f"Agent type '{agent_type}' is not registered. Available: {list(cls._REGISTRY.keys())}")
        return agent_cls(**kwargs)

    @classmethod
    def list_agents(cls) -> list[str]:
        """List all available agent types."""
        return list(cls._REGISTRY.keys())
