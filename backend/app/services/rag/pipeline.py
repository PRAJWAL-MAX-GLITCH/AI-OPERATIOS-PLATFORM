"""
RAG Ingestion & Indexing Pipeline
===================================
Orchestrates: Load → Clean → Chunk → Embed → Store in FAISS → Persist to DB.
This is the core workhorse of the RAG system.
"""
from __future__ import annotations
import uuid
import time
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.models.rag import KnowledgeBase, RAGDocument, RAGChunk, RAGIndex
from app.services.rag.loaders import load_document, supported_extensions
from app.services.rag.cleaner import clean_text
from app.services.rag.chunker import ChunkingEngine
from app.services.rag.embedder import EmbeddingEngine
from app.services.rag.vector_store import FAISSVectorStore
from app.core.exceptions import ResourceNotFoundError

logger = structlog.get_logger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DOCS_DIR = BASE_DIR / "documents"
DATA_DIR = BASE_DIR / "data" / "rag"


class IndexingPipeline:
    """
    Executes the full document → index pipeline for one document at a time.
    Idempotent: re-running on an already-indexed document will re-index it.
    """

    async def ingest_document(
        self,
        db: AsyncSession,
        knowledge_base: KnowledgeBase,
        file_path: str,
    ) -> RAGDocument:
        """
        Full pipeline for a single file:
        Load → Clean → Chunk → Embed → Store → DB persist.
        Returns the RAGDocument record.
        """
        path   = Path(file_path)
        ext    = path.suffix.lower().lstrip(".")
        kb_id  = knowledge_base.id

        # 1. Create or update DB record
        existing = await db.execute(
            select(RAGDocument).where(
                RAGDocument.knowledge_base_id == kb_id,
                RAGDocument.file_path == str(path),
            )
        )
        doc = existing.scalars().first()
        if not doc:
            doc = RAGDocument(
                knowledge_base_id=kb_id,
                filename=path.name,
                file_path=str(path),
                file_type=ext,
                status="processing",
            )
            db.add(doc)
        else:
            doc.status = "processing"
        await db.commit()
        await db.refresh(doc)

        try:
            # 2. Load
            raw_text, meta = load_document(str(path))
            doc.doc_metadata = meta
            doc.file_size_bytes = meta.get("file_size_bytes")

            # 3. Clean
            clean = clean_text(raw_text)
            if not clean.strip():
                raise ValueError("Document is empty after cleaning.")

            # 4. Chunk
            chunker  = ChunkingEngine(
                chunk_size=knowledge_base.chunk_size,
                chunk_overlap=knowledge_base.chunk_overlap,
                strategy="recursive",
            )
            chunks = chunker.chunk(clean, meta)

            # 5. Persist chunks to DB (delete old ones first)
            old_chunks = await db.execute(select(RAGChunk).where(RAGChunk.document_id == doc.id))
            for old in old_chunks.scalars().all():
                await db.delete(old)
            await db.flush()

            chunk_records = []
            for c in chunks:
                cr = RAGChunk(
                    document_id=doc.id,
                    knowledge_base_id=kb_id,
                    chunk_index=c.chunk_index,
                    text=c.text,
                    char_count=len(c.text),
                    token_estimate=c.token_estimate,
                    chunk_metadata={"source": path.name, **meta},
                )
                db.add(cr)
                chunk_records.append(cr)

            await db.commit()
            for cr in chunk_records:
                await db.refresh(cr)

            # 6. Embed
            embedder = EmbeddingEngine(knowledge_base.embedding_model)
            texts    = [cr.text for cr in chunk_records]
            vectors  = embedder.embed(texts)

            # 7. Store in FAISS
            index_path = str(DATA_DIR / "indexes" / f"{kb_id}.index")
            store = FAISSVectorStore(embedder.vector_dim, index_path)
            store.load()  # Load existing index (if any) to add incrementally
            store.add(vectors, [str(cr.id) for cr in chunk_records])
            store.save()

            # 8. Update RAGIndex record
            idx_rec = await db.get(RAGIndex, kb_id)
            if not idx_rec:
                # Use scalar sub-query result key check
                res = await db.execute(select(RAGIndex).where(RAGIndex.knowledge_base_id == kb_id))
                idx_rec = res.scalars().first()

            if idx_rec:
                idx_rec.total_vectors += len(chunk_records)
            else:
                idx_rec = RAGIndex(
                    knowledge_base_id=kb_id,
                    index_path=index_path,
                    embedding_model=knowledge_base.embedding_model,
                    vector_dim=embedder.vector_dim,
                    total_vectors=len(chunk_records),
                )
                db.add(idx_rec)

            doc.status       = "indexed"
            doc.total_chunks = len(chunk_records)
            knowledge_base.total_chunks    += len(chunk_records)
            knowledge_base.total_documents += 1
            knowledge_base.is_indexed       = True
            knowledge_base.index_path       = index_path

            await db.commit()
            await db.refresh(doc)

            logger.info("document_indexed", doc=path.name, chunks=len(chunk_records))
            return doc

        except Exception as exc:
            doc.status    = "failed"
            doc.error_msg = str(exc)
            await db.commit()
            logger.error("document_indexing_failed", doc=str(path), error=str(exc))
            raise

    async def ingest_directory(
        self,
        db: AsyncSession,
        knowledge_base: KnowledgeBase,
        directory: str = None,
    ) -> dict:
        """
        Discovers all supported documents in `directory` (defaults to /documents)
        and ingests them all.
        Returns a summary report.
        """
        docs_path = Path(directory) if directory else DOCS_DIR
        exts      = supported_extensions()

        files     = [f for f in docs_path.rglob("*") if f.suffix.lower() in exts and f.is_file()]
        logger.info("document_discovery", directory=str(docs_path), found=len(files))

        report = {"discovered": len(files), "indexed": 0, "failed": 0, "skipped": 0, "errors": []}

        for f in files:
            try:
                await self.ingest_document(db, knowledge_base, str(f))
                report["indexed"] += 1
            except Exception as exc:
                report["failed"] += 1
                report["errors"].append({"file": f.name, "error": str(exc)})

        return report


indexing_pipeline = IndexingPipeline()
