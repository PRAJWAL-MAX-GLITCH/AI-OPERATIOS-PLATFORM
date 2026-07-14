from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Any
import uuid


class KnowledgeBaseCreate(BaseModel):
    name:            str
    description:     str = ""
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size:      int = Field(default=512, ge=64, le=2048)
    chunk_overlap:   int = Field(default=64, ge=0, le=512)


class KnowledgeBaseResponse(BaseModel):
    id:              uuid.UUID
    name:            str
    description:     Optional[str]
    embedding_model: str
    chunk_size:      int
    chunk_overlap:   int
    is_indexed:      bool
    total_documents: int
    total_chunks:    int
    created_at:      datetime
    model_config = ConfigDict(from_attributes=True)


class RAGDocumentResponse(BaseModel):
    id:          uuid.UUID
    filename:    str
    file_type:   str
    status:      str
    total_chunks: int
    created_at:  datetime
    model_config = ConfigDict(from_attributes=True)


class SearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    chunk_id: str
    text:     str
    score:    float
    source:   str
    page:     Optional[int]


class SearchResponse(BaseModel):
    query:      str
    results:    list[SearchResult]
    context:    str
    latency_ms: float


class IndexingReportResponse(BaseModel):
    knowledge_base: str
    discovered:     int
    indexed:        int
    failed:         int
    skipped:        int
    errors:         list[dict]
    index_path:     Optional[str]
