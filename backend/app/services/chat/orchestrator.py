"""
RAG Chat Orchestrator
=====================
The central pipeline that coordinates all chat components.

Pipeline:
  User Question
    → SafetyGuard        (prompt injection / jailbreak / PII)
    → SessionManager     (create/load session)
    → MemoryManager      (load conversation history)
    → RAGService.search  (semantic retrieval)
    → CitationEngine     (build citations from chunks)
    → PromptBuilder      (assemble full LLM prompt)
    → LLMProviderFactory (select provider)
    → LLM.generate()     (call LLM)
    → MemoryManager      (persist messages)
    → CitationEngine     (persist citations)
    → AuditLog           (write event trail)
    → Response
"""
from __future__ import annotations
import time
import uuid
from typing import AsyncIterator, Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.chat import ConversationSession
from app.services.chat.safety_guard import SafetyGuard, SafetyCheckResult
from app.services.chat.session_manager import SessionManager
from app.services.chat.memory_manager import MemoryManager
from app.services.chat.prompt_builder import PromptBuilder
from app.services.chat.citation_engine import CitationEngine, CitationData
from app.services.chat.streaming import token_stream_to_sse
from app.services.chat.providers.factory import LLMProviderFactory
from app.services.rag_service import rag_service

logger = structlog.get_logger(__name__)
settings = get_settings()

# Singleton service instances (stateless, reuse across requests)
_safety     = SafetyGuard(enabled=settings.CHAT_ENABLE_SAFETY)
_sessions   = SessionManager()
_memory     = MemoryManager(max_turns=settings.CHAT_MAX_HISTORY_TURNS)
_prompts    = PromptBuilder(
    max_context_chars=settings.CHAT_MAX_CONTEXT_CHARS,
    max_history_turns=settings.CHAT_MAX_HISTORY_TURNS,
)
_citations  = CitationEngine()


class ChatOrchestrator:
    """Main RAG chat pipeline coordinator."""

    # ------------------------------------------------------------------
    # Non-Streaming Chat
    # ------------------------------------------------------------------

    async def chat(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        knowledge_base_id: uuid.UUID,
        question: str,
        session_id: uuid.UUID | None = None,
    ) -> dict:
        """
        Complete (non-streaming) RAG Q&A.
        Returns full response with citations.
        """
        t0 = time.perf_counter()

        # ── Step 1: Safety Check ──────────────────────────────────────
        safety_result = _safety.check(question, user_id=str(user_id))
        if not safety_result.passed:
            await _sessions.log_audit_event(
                db, session_id or uuid.uuid4(), user_id,
                event_type="safety_flagged",
                event_data={"threat": safety_result.threat_type, "detail": safety_result.detail},
                severity="critical",
            )
            return self._safety_refusal(safety_result)

        # Sanitize PII if detected
        clean_question = safety_result.sanitized if safety_result.sanitized else question

        # ── Step 2: Session ───────────────────────────────────────────
        session = await self._get_or_create_session(
            db, user_id, knowledge_base_id, session_id, clean_question
        )

        await _sessions.log_audit_event(db, session.id, user_id,
            event_type="question_asked",
            event_data={"question_chars": len(clean_question), "kb_id": str(knowledge_base_id)})

        # ── Step 3: Memory ────────────────────────────────────────────
        history = await _memory.get_history(db, session.id)

        # ── Step 4: RAG Retrieval ─────────────────────────────────────
        retrieval_result = await self._retrieve(db, knowledge_base_id, clean_question)
        raw_results      = retrieval_result.get("results", [])

        # ── Step 5: Citation Building ─────────────────────────────────
        citation_data = _citations.build_citations(raw_results)
        context       = _citations.build_context_with_citations(
            citation_data, max_chars=settings.CHAT_MAX_CONTEXT_CHARS
        )

        # ── Step 6: Prompt Assembly ───────────────────────────────────
        kb = await rag_service.get_knowledge_base(db, knowledge_base_id)
        messages = _prompts.build(
            question=clean_question,
            context=context,
            history=history,
            kb_name=kb.name,
        )

        # ── Step 7: LLM Call ──────────────────────────────────────────
        provider = LLMProviderFactory.create_from_settings()
        llm_cfg  = LLMProviderFactory.build_config(stream=False)

        await _sessions.log_audit_event(db, session.id, user_id,
            event_type="llm_invoked",
            event_data={"provider": provider.provider_name, "model": llm_cfg.model})

        llm_response = await self._call_llm(provider, messages, llm_cfg)

        # ── Step 8: Persist Messages ──────────────────────────────────
        await _memory.save_user_message(db, session.id, clean_question)
        asst_msg = await _memory.save_assistant_message(
            db, session.id,
            content=llm_response.content,
            model_used=llm_cfg.model,
            latency_ms=llm_response.latency_ms,
            has_citations=bool(citation_data),
        )

        # ── Step 9: Persist Citations ─────────────────────────────────
        if citation_data:
            await _citations.persist_citations(db, asst_msg.id, citation_data)

        # ── Step 10: Update Session Stats ─────────────────────────────
        await _memory.increment_session_stats(db, session, llm_response.total_tokens)
        await db.commit()

        # ── Step 11: Audit Log ────────────────────────────────────────
        latency_total = (time.perf_counter() - t0) * 1000
        await _sessions.log_audit_event(db, session.id, user_id,
            event_type="response_generated",
            event_data={
                "latency_ms": round(latency_total, 2),
                "tokens": llm_response.total_tokens,
                "citations": len(citation_data),
            })
        await db.commit()

        logger.info("chat_complete",
                    session=str(session.id), latency_ms=round(latency_total, 2),
                    tokens=llm_response.total_tokens, citations=len(citation_data))

        return {
            "session_id":  str(session.id),
            "answer":      llm_response.content,
            "citations":   _citations.format_for_response(citation_data),
            "model":       llm_cfg.model,
            "provider":    provider.provider_name,
            "latency_ms":  round(latency_total, 2),
            "total_tokens": llm_response.total_tokens,
        }

    # ------------------------------------------------------------------
    # Streaming Chat
    # ------------------------------------------------------------------

    async def chat_stream(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        knowledge_base_id: uuid.UUID,
        question: str,
        session_id: uuid.UUID | None = None,
    ) -> AsyncIterator[str]:
        """
        Streaming RAG Q&A via SSE.
        Yields SSE-formatted strings.
        """
        # ── Safety ────────────────────────────────────────────────────
        safety_result = _safety.check(question, user_id=str(user_id))
        if not safety_result.passed:
            from app.services.chat.streaming import format_sse_error, format_sse_done
            yield format_sse_error(f"Request blocked: {safety_result.threat_type} — {safety_result.detail}")
            yield format_sse_done()
            return

        clean_question = safety_result.sanitized if safety_result.sanitized else question

        # ── Session ───────────────────────────────────────────────────
        session = await self._get_or_create_session(
            db, user_id, knowledge_base_id, session_id, clean_question
        )

        # ── Memory & Retrieval ────────────────────────────────────────
        history = await _memory.get_history(db, session.id)
        retrieval_result = await self._retrieve(db, knowledge_base_id, clean_question)
        raw_results      = retrieval_result.get("results", [])

        # ── Citations & Context ───────────────────────────────────────
        citation_data = _citations.build_citations(raw_results)
        context       = _citations.build_context_with_citations(citation_data)

        # ── Prompt ────────────────────────────────────────────────────
        kb = await rag_service.get_knowledge_base(db, knowledge_base_id)
        messages = _prompts.build(clean_question, context, history, kb.name)

        # ── Stream LLM ────────────────────────────────────────────────
        provider = LLMProviderFactory.create_from_settings()
        llm_cfg  = LLMProviderFactory.build_config(stream=True)

        # Collect full content for persistence
        full_content = []

        try:
            raw_stream = provider.stream(messages, llm_cfg)

            async def content_collecting_stream():
                async for token in raw_stream:
                    full_content.append(token)
                    yield token

            async for sse_chunk in token_stream_to_sse(
                content_collecting_stream(),
                str(session.id),
                _citations.format_for_response(citation_data),
            ):
                yield sse_chunk

        finally:
            # Persist messages after streaming completes (even on cancel)
            combined = "".join(full_content)
            if combined:
                await _memory.save_user_message(db, session.id, clean_question)
                asst_msg = await _memory.save_assistant_message(
                    db, session.id, combined,
                    model_used=llm_cfg.model,
                    has_citations=bool(citation_data),
                )
                if citation_data:
                    await _citations.persist_citations(db, asst_msg.id, citation_data)
                await _memory.increment_session_stats(db, session)
                await db.commit()

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    async def _get_or_create_session(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        knowledge_base_id: uuid.UUID,
        session_id: uuid.UUID | None,
        question: str,
    ) -> ConversationSession:
        """Load existing session or create new one."""
        if session_id:
            session = await _sessions.get_session(db, session_id, user_id)
            if session:
                await _sessions.update_title_from_question(db, session, question)
                return session

        # Create new session
        session = await _sessions.create_session(
            db, user_id, knowledge_base_id=knowledge_base_id
        )
        await _sessions.update_title_from_question(db, session, question)
        return session

    async def _retrieve(
        self,
        db: AsyncSession,
        knowledge_base_id: uuid.UUID,
        question: str,
    ) -> dict:
        """Semantic retrieval from the knowledge base. Graceful on empty index."""
        try:
            return await rag_service.search(
                db, knowledge_base_id, question,
                top_k=settings.CHAT_TOP_K_RETRIEVAL,
            )
        except ValueError as exc:
            # Knowledge base not indexed yet — return empty context
            logger.warning("retrieval_skipped", reason=str(exc))
            return {"results": [], "context": "", "latency_ms": 0}

    async def _call_llm(self, provider, messages: list[dict], config) -> "LLMResponse":
        """Call LLM with graceful fallback on failure."""
        from app.services.chat.providers.base import LLMResponse
        try:
            return await provider.generate(messages, config)
        except Exception as exc:
            logger.error("llm_call_failed", provider=provider.provider_name, error=str(exc))
            # Return graceful fallback instead of crashing
            return LLMResponse(
                content=(
                    "I'm unable to generate a response at this time because the AI service "
                    f"({provider.provider_name}) is currently unavailable. "
                    "Please ensure the LLM provider is running and try again."
                ),
                model=config.model,
                provider=provider.provider_name,
                finish_reason="error",
            )

    def _safety_refusal(self, result: SafetyCheckResult) -> dict:
        """Build a safety refusal response."""
        return {
            "session_id":   None,
            "answer":       (
                "Your request could not be processed because it was flagged by our safety system. "
                f"Reason: {result.detail or result.threat_type}. "
                "Please rephrase your question and try again."
            ),
            "citations":    [],
            "model":        None,
            "provider":     None,
            "latency_ms":   0,
            "total_tokens": 0,
            "safety_flagged": True,
            "threat_type":  result.threat_type,
        }


chat_orchestrator = ChatOrchestrator()
