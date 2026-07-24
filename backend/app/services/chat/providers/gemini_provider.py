"""
Google Gemini LLM Provider
===========================
Google Gemini API integration.
Requires GEMINI_API_KEY in .env to activate.

Models: gemini-1.5-flash (fast), gemini-1.5-pro (quality)
"""
from __future__ import annotations
import asyncio
import time
from typing import AsyncIterator

import structlog

from app.services.chat.providers.base import LLMProvider, LLMConfig, LLMResponse

logger = structlog.get_logger(__name__)


class GeminiProvider(LLMProvider):
    """
    Google Gemini provider via google-generativeai SDK.
    Falls back gracefully if API key is not set.
    """

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self._api_key = api_key
        self._model   = model
        self._client  = None

    def _get_client(self):
        if self._client is None:
            try:
                import google.generativeai as genai  # type: ignore
                genai.configure(api_key=self._api_key)
                self._client = genai.GenerativeModel(self._model)
            except ImportError:
                raise RuntimeError(
                    "google-generativeai not installed. Run: pip install google-generativeai"
                )
        return self._client

    @property
    def provider_name(self) -> str:
        return "gemini"

    # ------------------------------------------------------------------
    # Complete Generation
    # ------------------------------------------------------------------

    async def generate(
        self,
        messages: list[dict],
        config: LLMConfig,
    ) -> LLMResponse:
        import google.generativeai as genai  # type: ignore

        if not self._api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured. Set it in .env.")

        # Convert OpenAI-style messages → Gemini format
        gemini_history, user_query = self._convert_messages(messages)
        t0 = time.perf_counter()

        client = self._get_client()
        try:
            gen_config = genai.types.GenerationConfig(  # type: ignore
                temperature=config.temperature,
                max_output_tokens=config.max_tokens,
            )
            # Run sync SDK in threadpool to keep async context
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.generate_content(
                    user_query,
                    generation_config=gen_config,
                )
            )

            latency_ms = (time.perf_counter() - t0) * 1000
            content    = response.text or ""
            usage      = response.usage_metadata

            logger.info("gemini_generate_complete",
                        model=config.model, latency_ms=round(latency_ms, 2))

            return LLMResponse(
                content=content,
                model=config.model,
                provider=self.provider_name,
                input_tokens=getattr(usage, "prompt_token_count", 0),
                output_tokens=getattr(usage, "candidates_token_count", 0),
                latency_ms=round(latency_ms, 2),
            )

        except Exception as exc:
            logger.error("gemini_error", error=str(exc))
            raise RuntimeError(f"Gemini API error: {exc}") from exc

    # ------------------------------------------------------------------
    # Streaming Generation
    # ------------------------------------------------------------------

    async def stream(
        self,
        messages: list[dict],
        config: LLMConfig,
    ) -> AsyncIterator[str]:
        import google.generativeai as genai  # type: ignore

        if not self._api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")

        _, user_query = self._convert_messages(messages)
        client = self._get_client()
        gen_config = genai.types.GenerationConfig(  # type: ignore
            temperature=config.temperature,
            max_output_tokens=config.max_tokens,
        )

        # Gemini streaming is sync — run each chunk step in threadpool
        loop    = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.generate_content(user_query, generation_config=gen_config, stream=True)
        )
        for chunk in response:
            text = getattr(chunk, "text", "") or ""
            if text:
                yield text

    # ------------------------------------------------------------------
    # Health Check
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        return bool(self._api_key)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _convert_messages(self, messages: list[dict]) -> tuple[list, str]:
        """
        Convert OpenAI-style messages to Gemini format.
        Returns (history, last_user_query).
        """
        history    = []
        last_query = ""
        for msg in messages:
            role    = msg["role"]
            content = msg["content"]
            if role == "user":
                last_query = content
            elif role == "assistant":
                history.append({"role": "model", "parts": [content]})
            # system messages are prepended to the last user query
            elif role == "system":
                last_query = content + "\n\n" + last_query

        # Build full prompt for simple cases
        full_prompt = "\n\n".join(
            f"[{m['role'].upper()}]\n{m['content']}"
            for m in messages
            if m["role"] != "system"
        )
        return history, full_prompt or last_query
