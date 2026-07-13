from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Any
import uuid


class DLTrainRequest(BaseModel):
    dataset_id:    uuid.UUID
    target_column: str
    problem_type:  str  # binary_classification | multiclass_classification | regression
    hyperparameters: dict[str, Any] = Field(default_factory=lambda: {
        "epochs":          50,
        "batch_size":      64,
        "learning_rate":   1e-3,
        "optimizer":       "adamw",
        "weight_decay":    1e-4,
        "dropout":         0.3,
        "hidden_dims":     [256, 128, 64],
        "scheduler":       "cosine",
        "patience":        10,
        "val_split":       0.2,
        "seed":            42,
        "grad_clip":       1.0,
    })


class DLPredictRequest(BaseModel):
    features: dict[str, Any]


class DLJobResponse(BaseModel):
    id:             uuid.UUID
    project_id:     uuid.UUID
    dataset_id:     uuid.UUID
    status:         str
    problem_type:   str
    target_column:  str
    architecture:   str
    current_epoch:  int
    total_epochs:   int
    best_val_loss:  Optional[float]
    best_epoch:     Optional[int]
    final_metrics:  Optional[dict[str, Any]]
    metrics_history: Optional[dict[str, Any]]
    mlflow_run_id:  Optional[str]
    created_at:     datetime

    model_config = ConfigDict(from_attributes=True)
