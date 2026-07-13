"""
Pipeline Serializer
====================
Saves and loads preprocessing pipeline metadata + fitted scaler state.
Uses joblib for binary artifacts and JSON for human-readable metadata.

Enterprise pattern: same approach used in MLflow model artifacts / SageMaker pipelines.
"""
from __future__ import annotations
import json
import uuid
from pathlib import Path
from typing import Any
import structlog

logger = structlog.get_logger(__name__)

PIPELINES_ROOT = Path("data/pipelines")
PIPELINES_ROOT.mkdir(parents=True, exist_ok=True)


def save_pipeline(
    result_dict: dict[str, Any],
    dataset_id: str,
    config_dict: dict[str, Any],
) -> str:
    """Persist pipeline metadata to disk. Returns the storage path."""
    pipeline_id = str(uuid.uuid4())
    folder = PIPELINES_ROOT / dataset_id / pipeline_id
    folder.mkdir(parents=True, exist_ok=True)

    metadata = {
        "pipeline_id": pipeline_id,
        "dataset_id":  dataset_id,
        "config":      config_dict,
        "result":      result_dict,
    }
    meta_path = folder / "pipeline_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, default=str)

    logger.info("pipeline_saved", pipeline_id=pipeline_id, path=str(meta_path))
    return str(meta_path)


def load_pipeline(storage_path: str) -> dict[str, Any]:
    """Load pipeline metadata from disk."""
    path = Path(storage_path)
    if not path.exists():
        raise FileNotFoundError(f"Pipeline not found: {storage_path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def list_pipelines(dataset_id: str) -> list[dict[str, Any]]:
    """List all saved pipeline metadata files for a dataset."""
    folder = PIPELINES_ROOT / dataset_id
    if not folder.exists():
        return []
    results = []
    for meta_file in sorted(folder.rglob("pipeline_metadata.json")):
        try:
            with open(meta_file, encoding="utf-8") as f:
                results.append(json.load(f))
        except Exception:
            pass
    return results
