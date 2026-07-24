"""
Agent Tool Registry
===================
Registers and provides access to all available agent tools.
"""
from __future__ import annotations
from typing import Dict, Type
import structlog
from app.services.agents.core.tool import Tool

logger = structlog.get_logger(__name__)


class ToolRegistry:
    """Registry for all tools available to agents."""
    
    _REGISTRY: Dict[str, Type[Tool]] = {}

    @classmethod
    def register(cls, tool_cls: Type[Tool]):
        """Decorator to register a tool class."""
        # Instantiate to get the name
        instance = tool_cls()
        cls._REGISTRY[instance.name] = tool_cls
        logger.debug("tool_registered", tool_name=instance.name)
        return tool_cls

    @classmethod
    def get_tool(cls, name: str) -> Tool:
        """Instantiate and return a tool by name."""
        tool_cls = cls._REGISTRY.get(name)
        if not tool_cls:
            raise ValueError(f"Tool '{name}' is not registered.")
        return tool_cls()

    @classmethod
    def get_all_tools(cls) -> list[Tool]:
        """Return instances of all registered tools."""
        return [tool_cls() for tool_cls in cls._REGISTRY.values()]
