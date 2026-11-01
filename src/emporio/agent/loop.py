"""Agent turn loop: model <-> typed tools, capped by ``max_tool_steps``.

The loop is provider-agnostic (any :class:`ChatModel`) and crash-safe: tool
validation failures arrive as JSON error payloads the model can self-correct,
and a runaway tool-calling streak ends in a polite Portuguese fallback.
"""

import sqlite3

from emporio.llm.base import ChatMessage, ChatModel
from emporio.tools import execute_tool, get_tool_definitions

from .prompt import SYSTEM_PROMPT

FALLBACK_TEXT = (
    "Tive uma instabilidade aqui no sistema. Pode repetir sua pergunta? "
    "Se preferir, chame a loja no WhatsApp (67) 3321-4500."
)


class Agent:
    """Stateful PT salesperson: keeps history, runs tool turns, returns text."""

    def __init__(
        self,
        model: ChatModel,
        connection: sqlite3.Connection,
        max_tool_steps: int = 8,
        system_prompt: str = SYSTEM_PROMPT,
    ) -> None:
        self.model = model
        self.connection = connection
        self.max_tool_steps = max_tool_steps
        self.history: list[ChatMessage] = [ChatMessage(role="system", content=system_prompt)]

    def reply(self, user_text: str) -> str:
        """Handle one user message through the tool loop; return the final text."""
        self.history.append(ChatMessage(role="user", content=user_text))
        definitions = get_tool_definitions()
        for _ in range(self.max_tool_steps):
            response = self.model.chat(self.history, definitions)
            self.history.append(
                ChatMessage(role="assistant", content=response.content, tool_calls=response.tool_calls)
            )
            if not response.tool_calls:
                return response.content or ""
            for call in response.tool_calls:
                output = execute_tool(call.name, self.connection, call.arguments)
                self.history.append(
                    ChatMessage(role="tool", content=output, tool_call_id=call.id)
                )
        self.history.append(ChatMessage(role="assistant", content=FALLBACK_TEXT))
        return FALLBACK_TEXT
