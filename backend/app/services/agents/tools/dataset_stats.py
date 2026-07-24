"""
Dataset Stats Tool
==================
Tool for agents to query dataset statistics.
"""
from typing import Type, Any
from pydantic import BaseModel, Field
import uuid

from app.services.agents.core.tool import Tool
from app.services.agents.tools.registry import ToolRegistry
from app.core.database import AsyncSessionLocal
from app.repositories.dataset import dataset_repo


class DatasetStatsArgs(BaseModel):
    dataset_id: str = Field(..., description="The UUID of the dataset to analyze.")


@ToolRegistry.register
class DatasetStatsTool(Tool):
    @property
    def name(self) -> str:
        return "get_dataset_stats"

    @property
    def description(self) -> str:
        return "Retrieve metadata and basic statistics about a dataset (e.g., format, file size, status)."

    @property
    def args_schema(self) -> Type[BaseModel]:
        return DatasetStatsArgs

    async def run(self, dataset_id: str) -> Any:
        try:
            ds_uuid = uuid.UUID(dataset_id)
        except ValueError:
            return "Invalid UUID format for dataset_id."

        async with AsyncSessionLocal() as db:
            dataset = await dataset_repo.get(db, id=ds_uuid)
            if not dataset:
                return f"Dataset with ID {dataset_id} not found."
            
            return {
                "name": dataset.name,
                "format": dataset.format,
                "status": dataset.status,
                "file_size_bytes": dataset.file_size_bytes,
                "description": dataset.description
            }
