"""
Pipeline Serializer
====================
Saves and loads trained models using joblib.
"""
from __future__ import annotations
import joblib
import json
import uuid
from pathlib import Path
from typing import Any
import structlog

logger = structlog.get_logger(__name__)

MODELS_ROOT = Path("data/models")
MODELS_ROOT.mkdir(parents=True, exist_ok=True)


def save_model(
    model: Any,
    dataset_id: str,
    project_id: str,
    metadata: dict[str, Any],
) -> str:
    """Persist model artifact and metadata to disk. Returns the storage path."""
    model_id = str(uuid.uuid4())
    folder = MODELS_ROOT / project_id / model_id
    folder.mkdir(parents=True, exist_ok=True)

    # Save artifact
    model_path = folder / "model.joblib"
    joblib.dump(model, model_path)

    # Save metadata
    metadata["model_id"] = model_id
    metadata["dataset_id"] = dataset_id
    metadata["project_id"] = project_id
    
    meta_path = folder / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, default=str)

    logger.info("model_saved", model_id=model_id, path=str(model_path))
    return str(model_path)


def load_model(storage_path: str) -> tuple[Any, dict[str, Any]]:
    """Load model artifact and metadata from disk."""
    path = Path(storage_path)
    if not path.exists():
        raise FileNotFoundError(f"Model not found: {storage_path}")
        
    folder = path.parent
    meta_path = folder / "metadata.json"
    
    model = joblib.load(path)
    
    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
        
    return model, metadata
