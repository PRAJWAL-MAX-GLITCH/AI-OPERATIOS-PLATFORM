"""
Document Ingestion Script (Idempotent)
=======================================
Safely re-runnable. Fetches existing KB if name already exists,
then re-triggers indexing for any new/unindexed documents.
"""
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.services.rag_service import rag_service
from app.models.rag import KnowledgeBase

KB_NAME = "Enterprise Core Knowledge Base"


async def main():
    async with AsyncSessionLocal() as db:

        # 1. Get-or-create Knowledge Base (idempotent)
        result = await db.execute(
            select(KnowledgeBase).where(KnowledgeBase.name == KB_NAME)
        )
        kb = result.scalar_one_or_none()

        if kb:
            print(f"[INFO] Found existing Knowledge Base: {kb.id} ({kb.name})")
        else:
            print("[INFO] Creating new Knowledge Base...")
            kb = await rag_service.create_knowledge_base(
                db=db,
                name=KB_NAME,
                description="Contains AI research papers, annual reports, and technical documentation.",
                chunk_size=512,
                chunk_overlap=64,
            )
            print(f"[INFO] Created Knowledge Base: {kb.id} ({kb.name})")

        # 2. Trigger Full Indexing (skips already-indexed docs)
        print("\n[INFO] Starting document indexing pipeline...")
        report = await rag_service.trigger_full_indexing(db, kb.id)

        print("\n=== Indexing Report ===")
        print(f"  Knowledge Base : {report['knowledge_base']}")
        print(f"  Discovered     : {report['discovered']}")
        print(f"  Indexed        : {report['indexed']}")
        print(f"  Skipped        : {report['skipped']}")
        print(f"  Failed         : {report['failed']}")
        print(f"  Index Path     : {report['index_path']}")

        if report["errors"]:
            print("\n  Errors:")
            for err in report["errors"]:
                print(f"    - {err['file']}: {err['error']}")

        # 3. Semantic search verification
        print("\n[INFO] Verifying semantic search...")
        try:
            search_result = await rag_service.search(db, kb.id, "What is attention mechanism?", top_k=3)
            print(f"  Query    : {search_result['query']}")
            print(f"  Results  : {len(search_result['results'])}")
            print(f"  Latency  : {search_result['latency_ms']} ms")
            if search_result["results"]:
                top = search_result["results"][0]
                print(f"  Top Hit  : {top['source']} (score={top['score']})")
        except Exception as e:
            print(f"  [WARN] Search test skipped: {e}")

        print("\n[DONE] Ingestion complete.")


if __name__ == "__main__":
    asyncio.run(main())
