"""
RAG API Router
==============
Knowledge bases, document management, search, and indexing endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid

from app.schemas.responses import ApiResponse
from app.schemas.rag import (
    KnowledgeBaseCreate, KnowledgeBaseResponse,
    RAGDocumentResponse, SearchRequest, SearchResponse, IndexingReportResponse
)
from app.services.rag_service import rag_service
from app.models.domain import User
from app.api.dependencies import get_db, get_current_user

router = APIRouter()


# ---------------------------------------------------------------------------
# Knowledge Base CRUD
# ---------------------------------------------------------------------------

@router.post(
    "/rag/knowledge-bases",
    response_model=ApiResponse[KnowledgeBaseResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_knowledge_base(
    request: KnowledgeBaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[KnowledgeBaseResponse]:
    """Create a new knowledge base."""
    kb = await rag_service.create_knowledge_base(
        db,
        name=request.name,
        description=request.description,
        embedding_model=request.embedding_model,
        chunk_size=request.chunk_size,
        chunk_overlap=request.chunk_overlap,
    )
    return ApiResponse(data=KnowledgeBaseResponse.model_validate(kb))


@router.get(
    "/rag/knowledge-bases",
    response_model=ApiResponse[List[KnowledgeBaseResponse]],
)
async def list_knowledge_bases(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[List[KnowledgeBaseResponse]]:
    """List all knowledge bases."""
    kbs = await rag_service.list_knowledge_bases(db)
    return ApiResponse(data=[KnowledgeBaseResponse.model_validate(kb) for kb in kbs])


@router.get(
    "/rag/knowledge-bases/{kb_id}",
    response_model=ApiResponse[KnowledgeBaseResponse],
)
async def get_knowledge_base(
    kb_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[KnowledgeBaseResponse]:
    kb = await rag_service.get_knowledge_base(db, kb_id)
    return ApiResponse(data=KnowledgeBaseResponse.model_validate(kb))


@router.delete("/rag/knowledge-bases/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    kb_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await rag_service.delete_knowledge_base(db, kb_id)


# ---------------------------------------------------------------------------
# Document Management
# ---------------------------------------------------------------------------

@router.get(
    "/rag/knowledge-bases/{kb_id}/documents",
    response_model=ApiResponse[List[RAGDocumentResponse]],
)
async def list_documents(
    kb_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[List[RAGDocumentResponse]]:
    docs = await rag_service.list_documents(db, kb_id)
    return ApiResponse(data=[RAGDocumentResponse.model_validate(d) for d in docs])


@router.delete("/rag/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await rag_service.delete_document(db, doc_id)


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------

@router.post(
    "/rag/knowledge-bases/{kb_id}/index",
    response_model=ApiResponse[IndexingReportResponse],
)
async def trigger_indexing(
    kb_id: uuid.UUID,
    directory: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[IndexingReportResponse]:
    """
    Trigger full document discovery + indexing pipeline.
    Call this AFTER placing documents in the /documents/ folder.
    Optional: pass a custom ?directory= path.
    """
    try:
        report = await rag_service.trigger_full_indexing(db, kb_id, directory)
        return ApiResponse(data=IndexingReportResponse(**report))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/rag/knowledge-bases/{kb_id}/discover",
    response_model=ApiResponse[List[str]],
)
async def discover_documents(
    kb_id: uuid.UUID,
    directory: Optional[str] = None,
    current_user: User = Depends(get_current_user),
) -> ApiResponse[List[str]]:
    """List all discoverable documents without indexing them."""
    files = rag_service.discover_documents(directory)
    return ApiResponse(data=files)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@router.post(
    "/rag/knowledge-bases/{kb_id}/search",
    response_model=ApiResponse[SearchResponse],
)
async def search(
    kb_id: uuid.UUID,
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[SearchResponse]:
    """
    Semantic search over indexed documents.
    Returns top-K relevant chunks with similarity scores and combined context.
    """
    try:
        result = await rag_service.search(db, kb_id, request.query, request.top_k)
        return ApiResponse(data=SearchResponse(**result))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
