"""
RAG Service
===========
Business logic layer — knowledge base CRUD, search, and watcher trigger.
"""
from __future__ import annotations
import time
import uuid
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.models.rag import KnowledgeBase, RAGDocument, RAGChunk, RAGIndex, RetrievalLog
from app.services.rag.pipeline import indexing_pipeline, DOCS_DIR
from app.services.rag.embedder import EmbeddingEngine
from app.services.rag.vector_store import FAISSVectorStore
from app.services.rag.retriever import RetrievalEngine, ContextBuilder
from app.core.exceptions import ResourceNotFoundError

logger = structlog.get_logger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "rag"


class RAGService:

    # ------------------------------------------------------------------
    # Knowledge Base Management
    # ------------------------------------------------------------------

    async def create_knowledge_base(
        self, db: AsyncSession, name: str, description: str = "",
        embedding_model: str = "all-MiniLM-L6-v2",
        chunk_size: int = 512, chunk_overlap: int = 64,
    ) -> KnowledgeBase:
        kb = KnowledgeBase(
            name=name, description=description,
            embedding_model=embedding_model,
            chunk_size=chunk_size, chunk_overlap=chunk_overlap,
        )
        db.add(kb)
        await db.commit()
        await db.refresh(kb)
        logger.info("knowledge_base_created", kb_id=str(kb.id), name=name)
        return kb

    async def list_knowledge_bases(self, db: AsyncSession) -> list[KnowledgeBase]:
        res = await db.execute(select(KnowledgeBase).order_by(KnowledgeBase.created_at.desc()))
        return list(res.scalars().all())

    async def get_knowledge_base(self, db: AsyncSession, kb_id: uuid.UUID) -> KnowledgeBase:
        kb = await db.get(KnowledgeBase, kb_id)
        if not kb:
            raise ResourceNotFoundError("KnowledgeBase", str(kb_id))
        return kb

    async def delete_knowledge_base(self, db: AsyncSession, kb_id: uuid.UUID) -> None:
        kb = await self.get_knowledge_base(db, kb_id)
        # Remove FAISS index from disk
        idx_path = DATA_DIR / "indexes" / f"{kb_id}.index"
        for p in [idx_path, idx_path.with_suffix(".meta.json")]:
            if p.exists():
                p.unlink()
        await db.delete(kb)
        await db.commit()

    # ------------------------------------------------------------------
    # Document Management
    # ------------------------------------------------------------------

    async def list_documents(self, db: AsyncSession, kb_id: uuid.UUID) -> list[RAGDocument]:
        res = await db.execute(
            select(RAGDocument).where(RAGDocument.knowledge_base_id == kb_id)
            .order_by(RAGDocument.created_at.desc())
        )
        return list(res.scalars().all())

    async def delete_document(self, db: AsyncSession, doc_id: uuid.UUID) -> None:
        doc = await db.get(RAGDocument, doc_id)
        if not doc:
            raise ResourceNotFoundError("RAGDocument", str(doc_id))
        await db.delete(doc)
        await db.commit()

    # ------------------------------------------------------------------
    # Indexing Trigger (Step 16 — POST-DOCUMENT-SETUP command)
    # ------------------------------------------------------------------

    async def trigger_full_indexing(
        self, db: AsyncSession, kb_id: uuid.UUID, directory: str = None
    ) -> dict:
        """
        ONE command that discovers, loads, cleans, chunks, embeds, and indexes
        all documents found in the directory (default: /documents/).
        Call AFTER placing documents in the folder.
        """
        kb = await self.get_knowledge_base(db, kb_id)
        report = await indexing_pipeline.ingest_directory(db, kb, directory)
        report["knowledge_base"] = kb.name
        report["index_path"]     = kb.index_path
        logger.info("full_indexing_triggered", **report)
        return report

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search(
        self,
        db: AsyncSession,
        kb_id: uuid.UUID,
        query: str,
        top_k: int = 5,
    ) -> dict:
        """
        Semantic search over the knowledge base.
        Returns ranked chunks with scores and context.
        """
        kb = await self.get_knowledge_base(db, kb_id)
        if not kb.is_indexed:
            raise ValueError(f"Knowledge base '{kb.name}' has not been indexed yet.")

        t0 = time.perf_counter()

        # 1. Load FAISS
        index_path = str(DATA_DIR / "indexes" / f"{kb_id}.index")
        embedder   = EmbeddingEngine(kb.embedding_model)
        store      = FAISSVectorStore(embedder.vector_dim, index_path)
        if not store.load():
            raise ValueError("FAISS index not found on disk. Please run indexing first.")

        # 2. Retrieve
        engine     = RetrievalEngine(embedder, store)
        raw_results = engine.search(query, top_k=top_k)

        # 3. Fetch chunk texts from DB
        enriched = []
        for chunk_id, score in raw_results:
            chunk = await db.get(RAGChunk, uuid.UUID(chunk_id))
            if chunk:
                enriched.append({
                    "chunk_id": chunk_id,
                    "text":     chunk.text,
                    "score":    round(score, 4),
                    "source":   chunk.chunk_metadata.get("source", "") if chunk.chunk_metadata else "",
                    "page":     chunk.page_number,
                })

        # 4. Build context
        builder = ContextBuilder(max_context_chars=4000)
        context = builder.build(enriched)

        latency_ms = (time.perf_counter() - t0) * 1000

        # 5. Audit log
        log = RetrievalLog(
            knowledge_base_id=kb_id,
            query=query,
            top_k=top_k,
            results_count=len(enriched),
            latency_ms=round(latency_ms, 2),
            retrieved_chunk_ids=[r["chunk_id"] for r in enriched],
        )
        db.add(log)
        await db.commit()

        logger.info("search_completed", kb=kb.name, results=len(enriched), latency_ms=round(latency_ms, 2))

        return {
            "query":     query,
            "results":   enriched,
            "context":   context,
            "latency_ms": round(latency_ms, 2),
        }

    # ------------------------------------------------------------------
    # Document Watcher — discover new files
    # ------------------------------------------------------------------

    def discover_documents(self, directory: str = None) -> list[str]:
        """
        Scans the documents directory for supported files.
        Returns list of file paths. Does NOT ingest automatically.
        """
        from app.services.rag.loaders import supported_extensions
        docs_path = Path(directory) if directory else DOCS_DIR
        exts      = supported_extensions()
        files     = [str(f) for f in docs_path.rglob("*") if f.suffix.lower() in exts and f.is_file()]
        logger.info("documents_discovered", count=len(files), directory=str(docs_path))
        return files


rag_service = RAGService()
