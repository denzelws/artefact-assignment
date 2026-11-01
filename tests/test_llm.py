"""Protocol and factory checks for the LLM layer (no network)."""

import http.client
import json
from unittest.mock import MagicMock, patch

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
    # Pass ollama_model explicitly: the developer's .env would otherwise leak in
    # (pydantic-settings reads it), and unit tests must be hermetic.
    model = get_chat_model(Settings(model_provider="ollama", ollama_model="llama3.1:8b"))
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


def _fake_http_ok(body: dict[str, object]) -> MagicMock:
    response = MagicMock()
    response.read.return_value = json.dumps(body).encode("utf-8")
    response.__enter__.return_value = response
    return response


def test_ollama_sends_temperature() -> None:
    client = OllamaClient(temperature=0.2)
    fake = _fake_http_ok({"message": {"role": "assistant", "content": "Oi"}})
    with patch("urllib.request.urlopen", return_value=fake) as urlopen:
        assert client.chat([ChatMessage(role="user", content="Oi")]).content == "Oi"
    sent = json.loads(urlopen.call_args[0][0].data.decode("utf-8"))
    assert sent["options"] == {"temperature": 0.2}


def test_factory_passes_temperature_through() -> None:
    model = get_chat_model(Settings(model_provider="ollama", temperature=0.7))
    assert isinstance(model, OllamaClient)
    assert model.temperature == 0.7
