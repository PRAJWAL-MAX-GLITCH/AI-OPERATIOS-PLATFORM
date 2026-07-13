"""
Training Configuration
======================
Config schemas for defining a training run.
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal, Optional, Any


class SplitConfig(BaseModel):
    strategy: Literal["random", "stratified"] = "random"
    test_size: float = Field(0.2, ge=0.01, le=0.99)
    random_state: int = 42


class TrainingConfig(BaseModel):
    problem_type: Literal["classification", "regression", "clustering"]
    target_column: Optional[str] = None
    algorithm: str = Field(..., description="Algorithm name e.g., 'random_forest'")
    split: SplitConfig = Field(default_factory=SplitConfig)
    parameters: dict[str, Any] = Field(default_factory=dict)
