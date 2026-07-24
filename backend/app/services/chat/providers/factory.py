"""
LLM Provider Factory
====================
Central registry for all LLM providers.
Provider Strategy Pattern — registering a new provider
requires ZERO changes to business logic.

Usage:
    provider = LLMProviderFactory.create("ollama")
    response = await provider.generate(messages, config)
"""
from __future__ import annotations
import structlog
from typing import Type

from app.services.chat.providers.base import LLMProvider, LLMConfig
from app.services.chat.providers.ollama_provider import OllamaProvider
from app.services.chat.providers.gemini_provider import GeminiProvider
from app.services.chat.providers.openai_provider import OpenAIProvider

logger = structlog.get_logger(__name__)


class LLMProviderFactory:
    """
    Registry-based factory for LLM providers.
    New providers self-register — no if/elif chains.
    """

    _REGISTRY: dict[str, Type[LLMProvider]] = {
        "ollama":    OllamaProvider,
        "gemini":    GeminiProvider,
        "openai":    OpenAIProvider,
        # Future providers register here:
        # "anthropic": AnthropicProvider,
        # "groq":      GroqProvider,
        # "mistral":   MistralProvider,
        # "azure":     AzureOpenAIProvider,
    }

    @classmethod
    def register(cls, name: str, provider_class: Type[LLMProvider]) -> None:
        """Register a new provider at runtime. Idempotent."""
        cls._REGISTRY[name.lower()] = provider_class
        logger.info("llm_provider_registered", provider=name)

    @classmethod
    def create(cls, provider_name: str, **kwargs) -> LLMProvider:
        """
        Instantiate a provider by name.
        kwargs are passed directly to the provider constructor.
        """
        name = provider_name.lower()
        cls_ = cls._REGISTRY.get(name)
        if not cls_:
            available = list(cls_._REGISTRY.keys()) if cls_ else list(cls._REGISTRY.keys())
            raise ValueError(
                f"Unknown LLM provider '{name}'. Available: {available}"
            )
        logger.info("llm_provider_created", provider=name)
        return cls_(**kwargs)

    @classmethod
    def create_from_settings(cls) -> LLMProvider:
        """
        Create the configured provider from app settings.
        This is the primary entrypoint for the application.
        """
        from app.core.config import get_settings
        settings = get_settings()

        provider = settings.LLM_PROVIDER.lower()

        if provider == "ollama":
            return OllamaProvider(base_url=settings.OLLAMA_BASE_URL)

        elif provider == "gemini":
            return GeminiProvider(
                api_key=settings.GEMINI_API_KEY,
                model=settings.GEMINI_MODEL,
            )

        elif provider == "openai":
            return OpenAIProvider(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
            )

        else:
            logger.warning("unknown_provider_fallback", provider=provider, fallback="ollama")
            return OllamaProvider(base_url=settings.OLLAMA_BASE_URL)

    @classmethod
    def build_config(cls, stream: bool = False) -> LLMConfig:
        """Build LLMConfig from application settings."""
        from app.core.config import get_settings
        settings = get_settings()

        provider = settings.LLM_PROVIDER.lower()
        if provider == "ollama":
            model = settings.OLLAMA_MODEL
        elif provider == "gemini":
            model = settings.GEMINI_MODEL
        elif provider == "openai":
            model = settings.OPENAI_MODEL
        else:
            model = settings.OLLAMA_MODEL

        return LLMConfig(
            model=model,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            timeout=settings.OLLAMA_TIMEOUT,
            max_retries=settings.LLM_MAX_RETRIES,
            retry_delay=settings.LLM_RETRY_DELAY,
            stream=stream,
        )

    @classmethod
    def list_providers(cls) -> list[str]:
        return list(cls._REGISTRY.keys())
