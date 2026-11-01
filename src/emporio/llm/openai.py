"""OpenAI chat client (opt-in provider, standard tool-calling spec).

Uses only the standard library (``urllib``) so Phase 2 adds no new
dependencies. Compatible with OpenAI's ``POST /v1/chat/completions`` and
any OpenAI-compatible endpoint via ``base_url``.
"""

import json
import urllib.error
import urllib.request
from typing import Any, Sequence

from .base import ChatMessage, ChatResponse, LLMError, ToolCallRequest, ToolDefinition

DEFAULT_BASE_URL = "https://api.openai.com/v1"


def _to_openai_message(message: ChatMessage) -> dict[str, Any]:
    """Convert a :class:`ChatMessage` to the OpenAI messages format."""
    if message.role == "tool":
        return {
            "role": "tool",
            "tool_call_id": message.tool_call_id or "",
            "content": message.content or "",
        }
    payload: dict[str, Any] = {"role": message.role, "content": message.content}
    if message.role == "assistant" and message.tool_calls:
        payload["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {"name": call.name, "arguments": json.dumps(call.arguments)},
            }
            for call in message.tool_calls
        ]
    return payload


def _parse_tool_calls(raw_calls: Any) -> list[ToolCallRequest]:
    """Normalize OpenAI ``tool_calls`` (arguments arrive as a JSON string)."""
    parsed: list[ToolCallRequest] = []
    if not isinstance(raw_calls, list):
        return parsed
    for index, raw in enumerate(raw_calls):
        if not isinstance(raw, dict):
            continue
        function = raw.get("function", {})
        if not isinstance(function, dict):
            continue
        name = str(function.get("name", ""))
        if not name:
            continue
        arguments = function.get("arguments", {})
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments) if arguments.strip() else {}
            except json.JSONDecodeError:
                arguments = {}
        if not isinstance(arguments, dict):
            arguments = {}
        parsed.append(
            ToolCallRequest(
                id=str(raw.get("id") or f"call_{index + 1}"),
                name=name,
                arguments=arguments,
            )
        )
    return parsed


class OpenAIClient:
    """Sync client for OpenAI chat completions with tool calling."""

    def __init__(
        self,
        api_key: str | None,
        model: str = "gpt-4o-mini",
        base_url: str = DEFAULT_BASE_URL,
    ) -> None:
        if not api_key:
            raise LLMError("OpenAI API key is missing (EMPORIO_OPENAI_API_KEY).")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def chat(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolDefinition] | None = None,
    ) -> ChatResponse:
        """Send ``messages`` to OpenAI and return text and/or tool calls."""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [_to_openai_message(message) for message in messages],
        }
        if tools:
            payload["tools"] = [tool.to_openai_schema() for tool in tools]
            payload["tool_choice"] = "auto"

        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
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
            raise LLMError(f"OpenAI request failed (HTTP {exc.code}): {detail}") from exc
        except urllib.error.URLError as exc:
            raise LLMError(f"Cannot reach OpenAI endpoint: {exc.reason}") from exc
        except (TimeoutError, json.JSONDecodeError) as exc:
            raise LLMError(f"Invalid response from OpenAI: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 - transport hiccups (dropped conn, reset)
            raise LLMError(f"OpenAI connection failed: {exc}") from exc

        try:
            message = data["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"Unexpected OpenAI response shape: {data!r}") from exc
        return ChatResponse(
            content=message.get("content"),
            tool_calls=_parse_tool_calls(message.get("tool_calls", [])),
        )
