"""
Document Search Tool
====================
Tool for agents to search the enterprise RAG knowledge base.
"""
from typing import Type, Any
from pydantic import BaseModel, Field
import uuid

from app.services.agents.core.tool import Tool
from app.services.agents.tools.registry import ToolRegistry
from app.core.database import AsyncSessionLocal
from app.services.rag_service import rag_service


class DocumentSearchArgs(BaseModel):
    knowledge_base_id: str = Field(..., description="The UUID of the knowledge base to search.")
    query: str = Field(..., description="The search query or question.")


@ToolRegistry.register
class DocumentSearchTool(Tool):
    @property
    def name(self) -> str:
        return "search_documents"

    @property
    def description(self) -> str:
        return "Search the enterprise knowledge base for relevant documents and context using vector search."

    @property
    def args_schema(self) -> Type[BaseModel]:
        return DocumentSearchArgs

    async def run(self, knowledge_base_id: str, query: str) -> Any:
        try:
            kb_uuid = uuid.UUID(knowledge_base_id)
        except ValueError:
            return "Invalid UUID format for knowledge_base_id."

        async with AsyncSessionLocal() as db:
            try:
                search_result = await rag_service.search(db, kb_uuid, query, top_k=3)
                
                if not search_result["results"]:
                    return "No relevant documents found."
                
                # Format a concise string for the agent
                output = f"Search Context for '{query}':\n\n"
                for i, res in enumerate(search_result["results"], 1):
                    source = res.get("source", "Unknown")
                    text = res.get("text", "").strip()
                    output += f"[Source {i}: {source}]\n{text}\n\n"
                    
                return output
            except Exception as e:
                return f"Failed to search documents: {str(e)}"
