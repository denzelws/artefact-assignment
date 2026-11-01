"""Ollama chat client (local default, ``llama3.1:8b``).

Uses only the standard library (``urllib``) so Phase 2 adds no new
dependencies. Targets Ollama's native ``POST /api/chat`` endpoint,
which accepts the same OpenAI-style ``tools`` envelope used in ``base.py``.
"""

import json
import urllib.error
import urllib.request
from typing import Any, Sequence

from .base import ChatMessage, ChatResponse, LLMError, ToolCallRequest, ToolDefinition


def _to_ollama_message(message: ChatMessage) -> dict[str, Any]:
    """Convert a :class:`ChatMessage` to Ollama's ``/api/chat`` format."""
    if message.role == "tool":
        # Ollama expects tool outputs as role="tool" with the result text.
        return {"role": "tool", "content": message.content or ""}
    payload: dict[str, Any] = {"role": message.role, "content": message.content or ""}
    if message.role == "assistant" and message.tool_calls:
        payload["tool_calls"] = [
            {"function": {"name": call.name, "arguments": call.arguments}}
            for call in message.tool_calls
        ]
    return payload


def _parse_tool_calls(raw_calls: Any) -> list[ToolCallRequest]:
    """Normalize Ollama ``tool_calls`` (ids optional, args dict or str)."""
    parsed: list[ToolCallRequest] = []
    if not isinstance(raw_calls, list):
        return parsed
    for index, raw in enumerate(raw_calls):
        function = raw.get("function", raw) if isinstance(raw, dict) else {}
        if not isinstance(function, dict):
            continue
        name = str(function.get("name", ""))
        if not name:
            continue
        arguments = function.get("arguments", {})
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments) if arguments else {}
            except json.JSONDecodeError:
                arguments = {}
        if not isinstance(arguments, dict):
            arguments = {}
        call_id = str(raw.get("id") or function.get("id") or f"call_{index + 1}")
        parsed.append(ToolCallRequest(id=call_id, name=name, arguments=arguments))
    return parsed


class OllamaClient:
    """Sync client for Ollama's ``/api/chat`` endpoint with tool calling."""

    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3.1:8b") -> None:
        self.host = host.rstrip("/")
        self.model = model

    def chat(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolDefinition] | None = None,
    ) -> ChatResponse:
        """Send ``messages`` to Ollama and return text and/or tool calls."""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [_to_ollama_message(message) for message in messages],
            "stream": False,
        }
        if tools:
            payload["tools"] = [tool.to_openai_schema() for tool in tools]

        request = urllib.request.Request(
            f"{self.host}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8")
            except Exception:  # noqa: BLE001 - best-effort error body
                detail = ""
            raise LLMError(f"Ollama request failed (HTTP {exc.code}): {detail}") from exc
        except urllib.error.URLError as exc:
            raise LLMError(f"Cannot reach Ollama at {self.host}: {exc.reason}") from exc
        except (TimeoutError, json.JSONDecodeError) as exc:
            raise LLMError(f"Invalid response from Ollama: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 - transport hiccups (dropped conn, reset)
            raise LLMError(f"Ollama connection failed: {exc}") from exc

        message = data.get("message", {}) if isinstance(data, dict) else {}
        return ChatResponse(
            content=message.get("content"),
            tool_calls=_parse_tool_calls(message.get("tool_calls", [])),
        )
