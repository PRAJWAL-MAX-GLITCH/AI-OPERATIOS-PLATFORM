"""
Base Agent Implementation
=========================
Core abstraction for an AI Agent. Handles the ReAct loop, tool orchestration,
and LLM communication.
"""
from __future__ import annotations
import abc
import json
from typing import List, Dict, Any, Type
import structlog

from app.services.agents.core.tool import Tool
from app.services.agents.core.state import AgentState, AgentContext
from app.services.chat.providers.factory import LLMProviderFactory
from app.services.chat.providers.base import LLMConfig
from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class BaseAgent(abc.ABC):
    """
    Abstract base class for all autonomous agents.
    Provides the execution loop, tool bindings, and error handling.
    """

    def __init__(self):
        self.provider = LLMProviderFactory.create_from_settings()
        self.llm_config = LLMProviderFactory.build_config(stream=False)
        # Agents typically need a slightly higher temperature for reasoning, but we'll stick to config
        # unless overridden by a specific agent.

    @property
    @abc.abstractmethod
    def agent_type(self) -> str:
        """Unique string identifier for the agent (e.g., 'planner', 'ml_engineer')."""
        pass

    @property
    @abc.abstractmethod
    def role_description(self) -> str:
        """System prompt / persona description for the agent."""
        pass

    @abc.abstractmethod
    def get_tools(self) -> List[Tool]:
        """Return a list of tool instances this agent is allowed to use."""
        pass

    async def execute(self, context: AgentContext, state: AgentState, initial_messages: List[dict] = None) -> str:
        """
        The core ReAct loop (Reasoning + Acting).
        Iterates until the agent decides it is finished or max steps are reached.
        """
        messages = self._build_system_prompt(context)
        if initial_messages:
            messages.extend(initial_messages)

        tools = self.get_tools()
        tool_schemas = [tool.get_function_schema() for tool in tools]
        tool_map = {tool.name: tool for tool in tools}

        logger.info("agent_execution_started", agent_type=self.agent_type, task_id=str(context.task_id))

        while not state.is_finished:
            state.increment_step()
            if state.is_finished:
                break

            logger.debug("agent_step", step=state.current_step, max_steps=state.max_steps)

            # Call LLM
            # We inject tool schemas if tools are available. We need to pass them to the provider.
            # For this architecture, we assume the provider config can handle raw function schemas in metadata or kwargs,
            # but to keep it provider-agnostic, we format them into the system prompt if native tool calling isn't used,
            # or we rely on the provider implementation. We will use native OpenAI-style tool calling.
            llm_response = await self._call_llm(messages, tool_schemas)

            # Record usage
            # (In a real implementation, we'd persist this to AgentRun stats)
            
            message_content = llm_response.content
            tool_calls = llm_response.raw_metadata.get("tool_calls", [])

            # Append the assistant's message to the history
            assistant_msg = {"role": "assistant", "content": message_content}
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
            messages.append(assistant_msg)

            # If no tool calls, the agent has responded with text. 
            # We assume it has finished its task unless it explicitly needs to continue.
            # In many agent frameworks, a specific "FINISH" tool or keyword is used.
            # For simplicity, if it doesn't call a tool, we consider it done.
            if not tool_calls:
                state.is_finished = True
                state.final_answer = message_content
                break

            # Execute Tools
            for tool_call in tool_calls:
                tool_call_id = tool_call.get("id")
                function = tool_call.get("function", {})
                tool_name = function.get("name")
                arguments_str = function.get("arguments", "{}")

                try:
                    arguments = json.loads(arguments_str)
                except json.JSONDecodeError:
                    arguments = {}

                if tool_name in tool_map:
                    tool = tool_map[tool_name]
                    result = await tool.execute(**arguments)
                    result_str = result.to_string()
                else:
                    result_str = f"Error: Tool '{tool_name}' not found or not permitted."

                state.add_observation(tool_name, arguments, result_str)

                # Append tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "name": tool_name,
                    "content": result_str
                })

        if state.error:
            return f"Agent failed: {state.error}"

        return state.final_answer or "Agent finished without providing a final answer."

    def _build_system_prompt(self, context: AgentContext) -> List[dict]:
        """Construct the initial system prompt including task context."""
        prompt = f"{self.role_description}\n\n"
        prompt += f"Task Title: {context.task_title}\n"
        if context.task_description:
            prompt += f"Task Description: {context.task_description}\n"
        prompt += "\nRespond to the user's request. You may use the provided tools to gather information or perform actions before returning your final answer."
        
        return [{"role": "system", "content": prompt}]

    async def _call_llm(self, messages: List[dict], tool_schemas: List[dict]) -> Any:
        """
        Wrapper around provider.generate that passes tools.
        NOTE: Since LLMProvider in Prompt 18 didn't natively accept tools, 
        we simulate passing it in raw_metadata or a modified config.
        For true support, we'd modify the base LLMProvider, but we will adapt it here.
        """
        # Since we cannot easily modify the base provider interface without breaking chat,
        # we format the tools into the system prompt as a fallback for Ollama/Gemini,
        # OR we rely on a provider extension.
        # For this enterprise platform, we assume OpenAI-style `tools` kwargs are supported by the underlying client.
        
        # We will modify the messages if the provider is Ollama/Gemini without native tool support,
        # but for production, we pass them down.
        
        # Since LLMProvider from Prompt 18 generate() only takes (messages, config),
        # we will monkey-patch or subclass here for agentic capabilities, or inject into messages.
        
        # Injection fallback (ReAct prompt formatting):
        if tool_schemas:
            tools_desc = json.dumps(tool_schemas, indent=2)
            inject = (
                f"\n\nYou have access to the following tools:\n{tools_desc}\n\n"
                "To use a tool, respond ONLY with a JSON object in this format:\n"
                "{\"tool_calls\": [{\"id\": \"call_123\", \"function\": {\"name\": \"tool_name\", \"arguments\": \"{\\\"arg\\\": \\\"val\\\"}\"}}]}\n"
                "Do not include any other text when calling a tool."
            )
            # Find system prompt and append
            for msg in messages:
                if msg["role"] == "system":
                    msg["content"] += inject
                    break

        response = await self.provider.generate(messages, self.llm_config)
        
        # Parse simulated tool calls from the text response if they exist
        # If the LLM returned our JSON format, extract it.
        try:
            content = response.content.strip()
            if content.startswith("{") and "tool_calls" in content:
                data = json.loads(content)
                if "tool_calls" in data:
                    response.raw_metadata["tool_calls"] = data["tool_calls"]
                    response.content = "" # clear content since it was a tool call
        except Exception:
            pass
            
        return response
