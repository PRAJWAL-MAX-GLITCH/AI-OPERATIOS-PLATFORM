"""
LLM Provider Base
=================
Abstract interface every LLM provider must implement.
Provider Strategy Pattern — adding a new provider requires ONLY:
  1. Subclass LLMProvider
  2. Register in LLMProviderFactory

NO business logic changes required.
"""
from __future__ import annotations
import abc
from dataclasses import dataclass, field
from typing import AsyncIterator, Optional


@dataclass
class LLMResponse:
    """Normalized response from any LLM provider."""
    content:        str
    model:          str
    provider:       str
    input_tokens:   int             = 0
    output_tokens:  int             = 0
    latency_ms:     float           = 0.0
    finish_reason:  str             = "stop"
    raw_metadata:   dict            = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class LLMConfig:
    """Unified config passed to every provider."""
    model:          str
    temperature:    float = 0.1
    max_tokens:     int   = 2048
    timeout:        int   = 120
    max_retries:    int   = 3
    retry_delay:    float = 1.0
    stream:         bool  = False


class LLMProvider(abc.ABC):
    """
    Abstract base class for all LLM providers.
    Implementations: OllamaProvider, GeminiProvider, OpenAIProvider, ...
    """

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider identifier."""
        ...

    @abc.abstractmethod
    async def generate(
        self,
        messages: list[dict],   # [{"role": "...", "content": "..."}]
        config: LLMConfig,
    ) -> LLMResponse:
        """Generate a complete (non-streaming) response."""
        ...

    @abc.abstractmethod
    async def stream(
        self,
        messages: list[dict],
        config: LLMConfig,
    ) -> AsyncIterator[str]:
        """Stream response tokens. Each yield is a text chunk."""
        ...

    @abc.abstractmethod
    async def health_check(self) -> bool:
        """Return True if the provider is reachable."""
        ...
