"""
Ollama LLM Provider
===================
Local LLM inference via Ollama REST API.
Default provider — free, private, runs on-device.

Supported models: llama3.2, llama3.1, mistral, phi3, gemma2, ...
"""
from __future__ import annotations
import asyncio
import json
import time
from typing import AsyncIterator

import httpx
import structlog

from app.services.chat.providers.base import LLMProvider, LLMConfig, LLMResponse

logger = structlog.get_logger(__name__)


class OllamaProvider(LLMProvider):
    """
    Connects to a local Ollama server at OLLAMA_BASE_URL.
    Automatically retries on transient failures.
    """

    def __init__(self, base_url: str = "http://localhost:11434"):
        self._base_url = base_url.rstrip("/")

    @property
    def provider_name(self) -> str:
        return "ollama"

    # ------------------------------------------------------------------
    # Complete Generation
    # ------------------------------------------------------------------

    async def generate(
        self,
        messages: list[dict],
        config: LLMConfig,
    ) -> LLMResponse:
        url     = f"{self._base_url}/api/chat"
        payload = {
            "model":    config.model,
            "messages": messages,
            "stream":   False,
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens,
            },
        }
        t0 = time.perf_counter()

        last_exc: Exception | None = None
        for attempt in range(1, config.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=config.timeout) as client:
                    resp = await client.post(url, json=payload)
                    resp.raise_for_status()
                    data = resp.json()

                latency_ms = (time.perf_counter() - t0) * 1000
                content    = data.get("message", {}).get("content", "")
                usage      = data.get("eval_count", 0)

                logger.info("ollama_generate_complete",
                            model=config.model, tokens=usage, latency_ms=round(latency_ms, 2))

                return LLMResponse(
                    content=content,
                    model=config.model,
                    provider=self.provider_name,
                    output_tokens=usage,
                    latency_ms=round(latency_ms, 2),
                    finish_reason=data.get("done_reason", "stop"),
                )

            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                last_exc = exc
                logger.warning("ollama_retry", attempt=attempt, error=str(exc))
                if attempt < config.max_retries:
                    await asyncio.sleep(config.retry_delay * attempt)

            except httpx.HTTPStatusError as exc:
                logger.error("ollama_http_error", status=exc.response.status_code, detail=exc.response.text)
                raise RuntimeError(f"Ollama HTTP error {exc.response.status_code}: {exc.response.text}") from exc

        raise RuntimeError(
            f"Ollama unavailable after {config.max_retries} attempts: {last_exc}"
        )

    # ------------------------------------------------------------------
    # Streaming Generation
    # ------------------------------------------------------------------

    async def stream(
        self,
        messages: list[dict],
        config: LLMConfig,
    ) -> AsyncIterator[str]:
        url     = f"{self._base_url}/api/chat"
        payload = {
            "model":    config.model,
            "messages": messages,
            "stream":   True,
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens,
            },
        }

        async with httpx.AsyncClient(timeout=config.timeout) as client:
            async with client.stream("POST", url, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        chunk = json.loads(line)
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            yield token
                        if chunk.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue

    # ------------------------------------------------------------------
    # Health Check
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False
