"""
Model Lookup Tool
=================
Tool for agents to query model details from the registry.
"""
from typing import Type, Any
from pydantic import BaseModel, Field
import uuid

from app.services.agents.core.tool import Tool
from app.services.agents.tools.registry import ToolRegistry
from app.core.database import AsyncSessionLocal
from app.repositories.model_registry import model_version_repo


class ModelLookupArgs(BaseModel):
    experiment_id: str = Field(..., description="The UUID of the experiment to lookup models for.")


@ToolRegistry.register
class ModelLookupTool(Tool):
    @property
    def name(self) -> str:
        return "lookup_experiment_models"

    @property
    def description(self) -> str:
        return "Retrieve the registered models and their evaluation metrics for a specific experiment."

    @property
    def args_schema(self) -> Type[BaseModel]:
        return ModelLookupArgs

    async def run(self, experiment_id: str) -> Any:
        try:
            exp_uuid = uuid.UUID(experiment_id)
        except ValueError:
            return "Invalid UUID format for experiment_id."

        async with AsyncSessionLocal() as db:
            models = await model_version_repo.get_by_experiment(db, experiment_id=exp_uuid)
            if not models:
                return f"No models found for experiment ID {experiment_id}."
            
            results = []
            for m in models:
                results.append({
                    "id": str(m.id),
                    "version": m.version,
                    "stage": m.stage,
                    "metrics": m.metrics
                })
            return results
