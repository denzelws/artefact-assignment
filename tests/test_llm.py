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
from emporio.llm.base import LLMError, ToolCallRequest


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


def _http_error(code: int, body: bytes) -> "urllib.error.HTTPError":
    import io
    import urllib.error

    return urllib.error.HTTPError(
        "http://x", code, "boom", {}, io.BytesIO(body)  # type: ignore[arg-type]
    )


def test_ollama_chat_parses_tool_calls() -> None:
    client = OllamaClient(model="llama3.2:3b")
    body = {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "search_products",
                        "arguments": '{"query": "Tagima"}',
                    }
                }
            ],
        }
    }
    tools = [ToolDefinition(name="search_products", description="Search")]
    with patch("urllib.request.urlopen", return_value=_fake_http_ok(body)) as urlopen:
        response = client.chat([ChatMessage(role="user", content="Tagima")], tools)
    assert len(response.tool_calls) == 1
    call = response.tool_calls[0]
    assert (call.name, call.arguments) == ("search_products", {"query": "Tagima"})
    assert call.id.startswith("call_")
    request = urlopen.call_args[0][0]
    assert request.full_url == "http://localhost:11434/api/chat"
    sent = json.loads(request.data.decode("utf-8"))
    assert sent["model"] == "llama3.2:3b"
    assert sent["tools"][0]["function"]["name"] == "search_products"


def test_ollama_tool_role_message_shape() -> None:
    client = OllamaClient()
    history = [
        ChatMessage(role="user", content="Oi"),
        ChatMessage(role="tool", content='{"ok": true}'),
    ]
    with patch("urllib.request.urlopen", return_value=_fake_http_ok({"message": {}})) as urlopen:
        client.chat(history)
    sent = json.loads(urlopen.call_args[0][0].data.decode("utf-8"))
    assert sent["messages"][1] == {"role": "tool", "content": '{"ok": true}'}


def test_ollama_http_error_details() -> None:
    import urllib.error

    client = OllamaClient()
    exc = _http_error(500, b"overloaded")
    try:
        with patch("urllib.request.urlopen", side_effect=exc):
            with pytest.raises(LLMError, match=r"HTTP 500.*overloaded"):
                client.chat([ChatMessage(role="user", content="Oi")])
    finally:
        exc.close()
    with patch(
        "urllib.request.urlopen", side_effect=urllib.error.URLError("refused")
    ):
        with pytest.raises(LLMError, match="Cannot reach Ollama"):
            client.chat([ChatMessage(role="user", content="Oi")])


def test_ollama_unreadable_error_body() -> None:
    import io
    import urllib.error

    class FailingBody(io.BytesIO):
        def read(self, *args: object, **kwargs: object) -> bytes:
            raise RuntimeError("gone")

    # BytesIO subclass: read() explodes (covers the best-effort branch) while
    # close() stays real, so nothing leaks at GC time.
    exc = urllib.error.HTTPError("http://x", 500, "boom", {}, FailingBody())
    client = OllamaClient()
    try:
        with patch("urllib.request.urlopen", side_effect=exc):
            with pytest.raises(LLMError, match=r"HTTP 500"):
                client.chat([ChatMessage(role="user", content="Oi")])
    finally:
        exc.close()


def test_ollama_invalid_json_body() -> None:
    response = MagicMock()
    response.read.return_value = b"not json{"
    response.__enter__.return_value = response
    client = OllamaClient()
    with patch("urllib.request.urlopen", return_value=response):
        with pytest.raises(LLMError, match="Invalid response"):
            client.chat([ChatMessage(role="user", content="Oi")])


def test_ollama_skips_nameless_tool_calls() -> None:
    from emporio.llm.ollama import _parse_tool_calls

    assert _parse_tool_calls("nope") == []
    assert _parse_tool_calls([{"function": {"arguments": {}}}]) == []
    assert _parse_tool_calls([{"function": {"name": "x", "arguments": "{bad"}}])[0].arguments == {}
    assert _parse_tool_calls([{"function": "nope"}]) == []
    assert _parse_tool_calls([{"function": {"name": "x", "arguments": ["a"]}}])[0].arguments == {}


def test_ollama_assistant_tool_calls_shape() -> None:
    from emporio.llm.ollama import _to_ollama_message

    message = ChatMessage(
        role="assistant",
        content=None,
        tool_calls=[
            ToolCallRequest(id="call_1", name="search_products", arguments={"query": "x"})
        ],
    )
    assert _to_ollama_message(message) == {
        "role": "assistant",
        "content": "",
        "tool_calls": [{"function": {"name": "search_products", "arguments": {"query": "x"}} }],
    }


def test_openai_chat_tool_round_trip() -> None:
    client = OpenAIClient(api_key="sk-test", model="gpt-4o-mini", temperature=0.2)
    body = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Achei!",
                    "tool_calls": [
                        {
                            "id": "call_9",
                            "type": "function",
                            "function": {"name": "get_store_info", "arguments": "{}"},
                        }
                    ],
                }
            }
        ]
    }
    history = [
        ChatMessage(role="user", content="Onde fica?"),
        ChatMessage(
            role="assistant",
            content=None,
            tool_calls=[],
        ),
        ChatMessage(role="tool", content='{"ok": true}', tool_call_id="call_9"),
    ]
    tools = [ToolDefinition(name="get_store_info", description="Info")]
    with patch("urllib.request.urlopen", return_value=_fake_http_ok(body)) as urlopen:
        response = client.chat(history, tools)
    assert response.content == "Achei!"
    assert [(c.id, c.name) for c in response.tool_calls] == [("call_9", "get_store_info")]
    request = urlopen.call_args[0][0]
    assert request.full_url == "https://api.openai.com/v1/chat/completions"
    assert request.get_header("Authorization") == "Bearer sk-test"
    sent = json.loads(request.data.decode("utf-8"))
    assert sent["temperature"] == 0.2
    assert sent["tool_choice"] == "auto"
    assert sent["messages"][2]["tool_call_id"] == "call_9"


def test_openai_needs_key() -> None:
    with pytest.raises(LLMError, match="API key is missing"):
        OpenAIClient(api_key=None)


def test_openai_unexpected_shape() -> None:
    client = OpenAIClient(api_key="sk-test")
    with patch("urllib.request.urlopen", return_value=_fake_http_ok({"nope": []})):
        with pytest.raises(LLMError, match="Unexpected OpenAI response shape"):
            client.chat([ChatMessage(role="user", content="Oi")])


def test_openai_transport_errors() -> None:
    import urllib.error

    client = OpenAIClient(api_key="sk-test")
    exc = _http_error(401, b"bad key")
    try:
        with patch("urllib.request.urlopen", side_effect=exc):
            with pytest.raises(LLMError, match=r"HTTP 401"):
                client.chat([ChatMessage(role="user", content="Oi")])
    finally:
        exc.close()
    with patch(
        "urllib.request.urlopen", side_effect=urllib.error.URLError("dns fail")
    ):
        with pytest.raises(LLMError, match="Cannot reach OpenAI"):
            client.chat([ChatMessage(role="user", content="Oi")])


def test_openai_skips_nameless_tool_calls() -> None:
    from emporio.llm.openai import _parse_tool_calls

    assert _parse_tool_calls(None) == []
    parsed = _parse_tool_calls(
        [
            "nope",
            {"function": "nope"},
            {"function": {}},
            {"function": {"name": "x", "arguments": "{bad"}},
            {"function": {"name": "y", "arguments": ["a"]}},
        ]
    )
    assert [(c.name, c.arguments) for c in parsed] == [("x", {}), ("y", {})]


def test_openai_assistant_tool_calls_shape() -> None:
    from emporio.llm.openai import _to_openai_message

    message = ChatMessage(
        role="assistant",
        content=None,
        tool_calls=[ToolCallRequest(id="call_2", name="get_store_info", arguments={})],
    )
    assert _to_openai_message(message) == {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_2",
                "type": "function",
                "function": {"name": "get_store_info", "arguments": "{}"},
            }
        ],
    }


def test_openai_timeout_and_generic_transport_errors() -> None:
    client = OpenAIClient(api_key="sk-test")
    with patch("urllib.request.urlopen", side_effect=TimeoutError("slow")):
        with pytest.raises(LLMError, match="Invalid response"):
            client.chat([ChatMessage(role="user", content="Oi")])
    import http.client

    with patch(
        "urllib.request.urlopen",
        side_effect=http.client.RemoteDisconnected("boom"),
    ):
        with pytest.raises(LLMError, match="OpenAI connection failed"):
            client.chat([ChatMessage(role="user", content="Oi")])


def test_openai_unreadable_error_body() -> None:
    import io
    import urllib.error

    class FailingBody(io.BytesIO):
        def read(self, *args: object, **kwargs: object) -> bytes:
            raise RuntimeError("gone")

    exc = urllib.error.HTTPError("http://x", 500, "boom", {}, FailingBody())
    client = OpenAIClient(api_key="sk-test")
    try:
        with patch("urllib.request.urlopen", side_effect=exc):
            with pytest.raises(LLMError, match=r"HTTP 500"):
                client.chat([ChatMessage(role="user", content="Oi")])
    finally:
        exc.close()
