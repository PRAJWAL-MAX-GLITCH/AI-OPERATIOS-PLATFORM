"""
Evaluation Configuration
========================
Schemas defining AutoML search space and cross-validation configs.
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal, Optional


class CVConfig(BaseModel):
    strategy: Literal["kfold", "stratified_kfold"] = "kfold"
    folds: int = Field(5, ge=2, le=10)
    random_state: int = 42


class AutoMLConfig(BaseModel):
    problem_type: Literal["classification", "regression", "clustering"]
    target_column: Optional[str] = None
    algorithms: Optional[list[str]] = None
    primary_metric: str = ""
    cv: CVConfig = Field(default_factory=CVConfig)
