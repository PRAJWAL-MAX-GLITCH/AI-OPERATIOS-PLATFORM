"""
OpenAI LLM Provider (Future-Ready Stub)
========================================
Placeholder implementation.
Activate by setting OPENAI_API_KEY and LLM_PROVIDER=openai in .env.
Install: pip install openai
"""
from __future__ import annotations
import asyncio
import time
from typing import AsyncIterator

import structlog

from app.services.chat.providers.base import LLMProvider, LLMConfig, LLMResponse

logger = structlog.get_logger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI / Azure OpenAI provider — stub ready for activation."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", base_url: str | None = None):
        self._api_key  = api_key
        self._model    = model
        self._base_url = base_url  # Override for Azure OpenAI
        self._client   = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import AsyncOpenAI  # type: ignore
                kwargs = {"api_key": self._api_key}
                if self._base_url:
                    kwargs["base_url"] = self._base_url
                self._client = AsyncOpenAI(**kwargs)
            except ImportError:
                raise RuntimeError("openai package not installed. Run: pip install openai")
        return self._client

    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate(self, messages: list[dict], config: LLMConfig) -> LLMResponse:
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        client = self._get_client()
        t0 = time.perf_counter()

        response = await client.chat.completions.create(
            model=config.model,
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )

        latency_ms = (time.perf_counter() - t0) * 1000
        content    = response.choices[0].message.content or ""
        usage      = response.usage

        logger.info("openai_generate_complete", model=config.model, latency_ms=round(latency_ms, 2))

        return LLMResponse(
            content=content,
            model=config.model,
            provider=self.provider_name,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            latency_ms=round(latency_ms, 2),
        )

    async def stream(self, messages: list[dict], config: LLMConfig) -> AsyncIterator[str]:
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        client = self._get_client()
        response = await client.chat.completions.create(
            model=config.model,
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            stream=True,
        )
        async for chunk in response:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                yield delta

    async def health_check(self) -> bool:
        return bool(self._api_key)
