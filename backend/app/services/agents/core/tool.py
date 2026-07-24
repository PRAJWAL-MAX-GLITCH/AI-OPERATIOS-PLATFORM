"""
Agent Tool Abstraction
======================
Base class for all tools that an agent can invoke.
Supports synchronous and asynchronous execution, parameter validation via Pydantic,
and graceful error handling.
"""
from __future__ import annotations
import abc
import inspect
from typing import Any, Type, Optional, Callable
from pydantic import BaseModel
import structlog
import traceback

logger = structlog.get_logger(__name__)


class ToolResult:
    """Standardized output format for a tool execution."""
    def __init__(self, is_success: bool, output: Any, error: Optional[str] = None):
        self.is_success = is_success
        self.output = output
        self.error = error

    def to_string(self) -> str:
        """String representation returned to the LLM."""
        if self.is_success:
            return str(self.output)
        return f"Error executing tool: {self.error}"


class Tool(abc.ABC):
    """
    Abstract Base Class for an Agent Tool.
    Subclasses must define `name`, `description`, `args_schema`, and implement `run()`.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Name of the tool (must be unique, no spaces, e.g., 'get_dataset_stats')."""
        pass

    @property
    @abc.abstractmethod
    def description(self) -> str:
        """
        Detailed description of what the tool does and when to use it.
        This is passed to the LLM to help it decide when to invoke the tool.
        """
        pass

    @property
    @abc.abstractmethod
    def args_schema(self) -> Type[BaseModel]:
        """Pydantic model defining the expected arguments."""
        pass

    @abc.abstractmethod
    async def run(self, **kwargs) -> Any:
        """
        The actual logic of the tool.
        Can be an async function.
        """
        pass

    async def execute(self, **kwargs) -> ToolResult:
        """
        Wrapper around run() that handles validation and error catching.
        Never throws an exception back to the orchestrator; instead, returns a ToolResult.
        """
        try:
            # Validate arguments using the provided Pydantic schema
            validated_args = self.args_schema(**kwargs)
            
            # Execute tool logic
            logger.info("tool_execution_start", tool=self.name, args=kwargs)
            result = await self.run(**validated_args.model_dump())
            logger.info("tool_execution_success", tool=self.name)
            
            return ToolResult(is_success=True, output=result)
        
        except Exception as e:
            error_msg = str(e)
            logger.error("tool_execution_failed", tool=self.name, error=error_msg, exc_info=True)
            return ToolResult(is_success=False, output=None, error=error_msg)

    def get_function_schema(self) -> dict:
        """
        Generate OpenAI-compatible function calling schema.
        """
        schema = self.args_schema.model_json_schema()
        
        # OpenAI doesn't allow 'title' in the parameters root
        if 'title' in schema:
            del schema['title']

        return {
            "name": self.name,
            "description": self.description,
            "parameters": schema
        }
