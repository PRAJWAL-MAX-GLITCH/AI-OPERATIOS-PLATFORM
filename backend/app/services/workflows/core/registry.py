"""
Workflow Registry
=================
Holds predefined workflow and pipeline templates.
"""

from typing import Dict, Any

class WorkflowRegistry:
    """Predefined pipeline templates for the Enterprise AI Platform."""
    
    _templates: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(cls, name: str, dag: Dict[str, Any]):
        cls._templates[name] = dag

    @classmethod
    def get_template(cls, name: str) -> Dict[str, Any]:
        return cls._templates.get(name)

# --- Predefined Pipelines ---

WorkflowRegistry.register("validation_pipeline", {
    "tasks": [
        {"id": "dataset_upload", "type": "dataset_ingestion"},
        {"id": "validate_schema", "type": "schema_validation"},
        {"id": "analyze_data", "type": "dataset_analysis"}
    ],
    "edges": [
        {"from": "dataset_upload", "to": "validate_schema"},
        {"from": "validate_schema", "to": "analyze_data"}
    ]
})

WorkflowRegistry.register("training_pipeline", {
    "tasks": [
        {"id": "preprocess", "type": "data_preprocessing"},
        {"id": "train_model", "type": "model_training"},
        {"id": "evaluate_model", "type": "model_evaluation"},
        {"id": "register_model", "type": "model_registration"}
    ],
    "edges": [
        {"from": "preprocess", "to": "train_model"},
        {"from": "train_model", "to": "evaluate_model"},
        {"from": "evaluate_model", "to": "register_model"}
    ]
})

WorkflowRegistry.register("rag_indexing_pipeline", {
    "tasks": [
        {"id": "ingest_document", "type": "document_ingestion"},
        {"id": "extract_text", "type": "text_extraction"},
        {"id": "chunk_text", "type": "text_chunking"},
        {"id": "embed_chunks", "type": "embedding_generation"},
        {"id": "index_vectors", "type": "vector_indexing"}
    ],
    "edges": [
        {"from": "ingest_document", "to": "extract_text"},
        {"from": "extract_text", "to": "chunk_text"},
        {"from": "chunk_text", "to": "embed_chunks"},
        {"from": "embed_chunks", "to": "index_vectors"}
    ]
})

WorkflowRegistry.register("agent_pipeline", {
    "tasks": [
        {"id": "planner", "type": "agent_execution"},
        {"id": "worker", "type": "agent_execution"},
        {"id": "report", "type": "agent_execution"}
    ],
    "edges": [
        {"from": "planner", "to": "worker"},
        {"from": "worker", "to": "report"}
    ]
})
