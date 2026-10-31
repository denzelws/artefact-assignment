"""Core chat types and the ``ChatModel`` protocol.

The agent loop only depends on these types. Provider clients
(``ollama.py``, ``openai.py``) implement :class:`ChatModel` without
leaking provider-specific payloads into the agent.
"""

from typing import Any, Literal, Protocol, Sequence

from pydantic import BaseModel, Field

ChatRole = Literal["system", "user", "assistant", "tool"]


class ToolCallRequest(BaseModel):
    """A single function call requested by the model."""

    id: str = Field(description="Unique call id, used to match tool results.")
    name: str = Field(description="Tool (function) name to invoke.")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Decoded JSON arguments for the tool."
    )


class ChatMessage(BaseModel):
    """One turn in the conversation, including tool results."""

    role: ChatRole
    content: str | None = Field(default=None, description="Text content, may be empty.")
    tool_calls: list[ToolCallRequest] = Field(default_factory=list)
    tool_call_id: str | None = Field(
        default=None, description="Set only on role='tool' to match a request."
    )


class ChatResponse(BaseModel):
    """Model output for one step: text and/or tool call requests."""

    content: str | None = Field(default=None, description="Assistant text, if any.")
    tool_calls: list[ToolCallRequest] = Field(default_factory=list)


class ToolDefinition(BaseModel):
    """Pydantic-friendly tool declaration handed to the model.

    ``parameters`` is a JSON Schema object (as produced by
    ``MyArgs.model_json_schema()`` in the tools package). Both providers
    accept the same OpenAI-style ``{"type": "function", ...}`` envelope,
    so this class converts itself with :meth:`to_openai_schema`.
    """

    name: str
    description: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)

    def to_openai_schema(self) -> dict[str, Any]:
        """Return the OpenAI ``tools[]`` entry for this tool."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters or {"type": "object", "properties": {}},
            },
        }


class ChatModel(Protocol):
    """Sync chat interface every provider must implement."""

    def chat(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolDefinition] | None = None,
    ) -> ChatResponse:
        """Generate one assistant step for ``messages``, optionally using ``tools``."""
        ...  # pragma: no cover - protocol stub


class LLMError(RuntimeError):
    """Raised when a provider request fails (network, auth, bad payload)."""
