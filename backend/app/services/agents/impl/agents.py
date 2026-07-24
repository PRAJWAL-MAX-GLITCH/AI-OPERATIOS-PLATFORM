"""
Enterprise Agents Implementation
================================
Specific autonomous agents that accomplish enterprise tasks.
"""
from typing import List
from app.services.agents.core.base import BaseAgent
from app.services.agents.core.registry import AgentRegistry
from app.services.agents.core.tool import Tool
from app.services.agents.tools.registry import ToolRegistry


@AgentRegistry.register("planner")
class PlannerAgent(BaseAgent):
    @property
    def agent_type(self) -> str:
        return "planner"

    @property
    def role_description(self) -> str:
        return (
            "You are the Lead Project Planner. Your job is to take a high-level user request "
            "and break it down into a sequence of actionable steps. You orchestrate other agents "
            "but you do not write code or analyze data yourself."
        )

    def get_tools(self) -> List[Tool]:
        return []


@AgentRegistry.register("dataset_analyst")
class DatasetAnalysisAgent(BaseAgent):
    @property
    def agent_type(self) -> str:
        return "dataset_analyst"

    @property
    def role_description(self) -> str:
        return (
            "You are a Senior Data Analyst. Your job is to analyze uploaded datasets, "
            "extract statistics, and summarize the data schema and quality."
        )

    def get_tools(self) -> List[Tool]:
        return [ToolRegistry.get_tool("get_dataset_stats")]


@AgentRegistry.register("ml_engineer")
class MLEngineerAgent(BaseAgent):
    @property
    def agent_type(self) -> str:
        return "ml_engineer"

    @property
    def role_description(self) -> str:
        return (
            "You are a Principal Machine Learning Engineer. Your job is to suggest algorithms, "
            "preprocessing steps, and evaluation metrics for a given dataset and problem type. "
            "You can look up previous models to inform your decisions."
        )

    def get_tools(self) -> List[Tool]:
        return [ToolRegistry.get_tool("lookup_experiment_models")]


@AgentRegistry.register("rag_researcher")
class RAGResearchAgent(BaseAgent):
    @property
    def agent_type(self) -> str:
        return "rag_researcher"

    @property
    def role_description(self) -> str:
        return (
            "You are a dedicated Enterprise Researcher. Your job is to search the internal "
            "knowledge base to find answers to complex questions, summarize retrieved documents, "
            "and provide accurate citations."
        )

    def get_tools(self) -> List[Tool]:
        return [ToolRegistry.get_tool("search_documents")]


@AgentRegistry.register("report_generator")
class ReportGeneratorAgent(BaseAgent):
    @property
    def agent_type(self) -> str:
        return "report_generator"

    @property
    def role_description(self) -> str:
        return (
            "You are a Technical Writer and Report Generator. Your job is to synthesize "
            "the findings from other agents into a well-structured, professional Markdown report."
        )

    def get_tools(self) -> List[Tool]:
        return []
