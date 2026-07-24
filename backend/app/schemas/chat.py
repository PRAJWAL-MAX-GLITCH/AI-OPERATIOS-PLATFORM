"""
Chat API Schemas
================
Pydantic models for all chat endpoints.
"""
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List
import uuid


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    """Request body for POST /chat and POST /chat/stream."""
    knowledge_base_id: uuid.UUID                  = Field(..., description="Target knowledge base UUID")
    question:          str                         = Field(..., min_length=1, max_length=4000)
    session_id:        Optional[uuid.UUID]         = Field(None, description="Continue existing session")


# ---------------------------------------------------------------------------
# Citation Schema
# ---------------------------------------------------------------------------

class CitationResponse(BaseModel):
    chunk_id:         Optional[str]
    source_document:  str
    page_number:      Optional[int]
    excerpt:          Optional[str]
    similarity_score: Optional[float]
    confidence:       str  # high | medium | low


# ---------------------------------------------------------------------------
# Chat Response Schema
# ---------------------------------------------------------------------------

class ChatResponse(BaseModel):
    session_id:     Optional[str]
    answer:         str
    citations:      List[CitationResponse]  = []
    model:          Optional[str]
    provider:       Optional[str]
    latency_ms:     float                   = 0.0
    total_tokens:   int                     = 0
    safety_flagged: bool                    = False


# ---------------------------------------------------------------------------
# Session Schemas
# ---------------------------------------------------------------------------

class SessionSummary(BaseModel):
    id:               uuid.UUID
    title:            Optional[str]
    llm_provider:     str
    llm_model:        str
    total_messages:   int
    total_tokens_used: int
    created_at:       datetime
    updated_at:       datetime

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    id:           uuid.UUID
    role:         str
    content:      str
    token_count:  int
    latency_ms:   Optional[float]
    model_used:   Optional[str]
    has_citations: bool
    created_at:   datetime

    model_config = ConfigDict(from_attributes=True)


class SessionDetailResponse(BaseModel):
    id:               uuid.UUID
    title:            Optional[str]
    knowledge_base_id: Optional[uuid.UUID]
    llm_provider:     str
    llm_model:        str
    total_messages:   int
    total_tokens_used: int
    messages:         List[MessageResponse] = []
    created_at:       datetime
    updated_at:       datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Citation List Schema
# ---------------------------------------------------------------------------

class SessionCitationResponse(BaseModel):
    id:               uuid.UUID
    message_id:       uuid.UUID
    chunk_id:         Optional[str]
    source_document:  str
    page_number:      Optional[int]
    excerpt:          Optional[str]
    similarity_score: Optional[float]
    confidence:       str
    created_at:       datetime

    model_config = ConfigDict(from_attributes=True)
