"""LLM client protocol and provider implementations."""

from .base import (
    ChatMessage,
    ChatModel,
    ChatResponse,
    LLMError,
    ToolCallRequest,
    ToolDefinition,
)
from .ollama import OllamaClient
from .openai import OpenAIClient

__all__ = [
    "ChatMessage",
    "ChatModel",
    "ChatResponse",
    "LLMError",
    "OllamaClient",
    "OpenAIClient",
    "ToolCallRequest",
    "ToolDefinition",
    "get_chat_model",
]


def get_chat_model(settings: object | None = None) -> ChatModel:
    """Instantiate the configured provider from :class:`Settings`.

    Lazily imports ``config`` to avoid a hard dependency cycle: ``llm``
    never imports ``config`` at module load time.
    """
    from emporio.config import Settings, get_settings

    resolved: Settings = settings if isinstance(settings, Settings) else get_settings()
    if resolved.model_provider == "openai":
        return OpenAIClient(
            api_key=resolved.openai_api_key,
            model=resolved.openai_model,
            temperature=resolved.temperature,
        )
    return OllamaClient(host=resolved.ollama_host, model=resolved.ollama_model, temperature=resolved.temperature)
