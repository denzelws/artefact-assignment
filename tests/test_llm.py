"""Protocol and factory checks for the LLM layer (no network)."""

import http.client
from unittest.mock import patch

import pytest

from emporio.config import Settings
from emporio.llm import (
    ChatMessage,
    OllamaClient,
    OpenAIClient,
    ToolDefinition,
    get_chat_model,
)
from emporio.llm.base import LLMError


def test_clients_implement_chat() -> None:
    assert hasattr(OllamaClient, "chat") and hasattr(OpenAIClient, "chat")


def test_factory_defaults_to_ollama() -> None:
    model = get_chat_model(Settings(model_provider="ollama"))
    assert isinstance(model, OllamaClient)
    assert model.model == "llama3.1:8b"


def test_factory_openai_needs_key() -> None:
    with pytest.raises(LLMError):
        get_chat_model(Settings(model_provider="openai", openai_api_key=None))


def test_tool_schema_envelope() -> None:
    tool = ToolDefinition(
        name="search_products",
        description="Search",
        parameters={"type": "object", "properties": {"q": {"type": "string"}}},
    )
    schema = tool.to_openai_schema()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "search_products"


def test_message_round_trip_shape() -> None:
    message = ChatMessage(role="user", content="Olá!")
    assert message.role == "user"
    assert message.content == "Olá!"
    assert message.tool_calls == []


def test_dropped_connection_becomes_llm_error() -> None:
    client = OllamaClient()
    with patch("urllib.request.urlopen", side_effect=http.client.RemoteDisconnected("boom")):
        with pytest.raises(LLMError, match="Ollama connection failed"):
            client.chat([ChatMessage(role="user", content="Oi")])
