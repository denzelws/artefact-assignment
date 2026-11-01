"""Agent loop checks with a scripted fake model (no network, real tools)."""

import json
import sqlite3
from pathlib import Path
from typing import Sequence

import pytest

from emporio.agent import FALLBACK_TEXT, SYSTEM_PROMPT, Agent
from emporio.data import connect, load_database
from emporio.llm.base import ChatMessage, ChatResponse, ToolCallRequest, ToolDefinition


class FakeModel:
    """Canned ChatModel: pops one scripted response per chat() call."""

    def __init__(self, script: list[ChatResponse]) -> None:
        self.script = list(script)
        self.calls: list[tuple[list[ChatMessage], object]] = []

    def chat(
        self,
        messages: Sequence[ChatMessage],
        tools: Sequence[ToolDefinition] | None = None,
    ) -> ChatResponse:
        self.calls.append((list(messages), tools))
        assert self.script, "FakeModel ran out of scripted responses"
        return self.script.pop(0)


@pytest.fixture()
def agent_connection(tmp_path: Path) -> sqlite3.Connection:
    load_database(tmp_path / "agent.sqlite", "data")
    conn = connect(tmp_path / "agent.sqlite")
    yield conn
    conn.close()


def _tool_call(name: str, arguments: dict[str, object]) -> ChatResponse:
    return ChatResponse(
        content=None,
        tool_calls=[ToolCallRequest(id="call_1", name=name, arguments=arguments)],
    )


def test_system_prompt_is_portuguese_persona() -> None:
    assert "Empório da Música" in SYSTEM_PROMPT
    assert "NUNCA informe preço" in SYSTEM_PROMPT
    assert "24 horas úteis" in SYSTEM_PROMPT


def test_text_answer_returns_directly(agent_connection: sqlite3.Connection) -> None:
    agent = Agent(FakeModel([ChatResponse(content="Olá! Como posso ajudar?")]), agent_connection)
    assert agent.reply("Oi") == "Olá! Como posso ajudar?"
    roles = [message.role for message in agent.history]
    assert roles == ["system", "user", "assistant"]


def test_tool_result_flows_back_to_model(agent_connection: sqlite3.Connection) -> None:
    model = FakeModel(
        [
            _tool_call("search_products", {"category": "ukuleles", "limit": 2}),
            ChatResponse(content="Achei 2 ukuleles para você!"),
        ]
    )
    agent = Agent(model, agent_connection)
    assert agent.reply("quero um ukulele") == "Achei 2 ukuleles para você!"

    tool_messages = [message for message in agent.history if message.role == "tool"]
    assert len(tool_messages) == 1
    payload = json.loads(tool_messages[0].content or "{}")
    assert payload["ok"] and len(payload["result"]) == 2
    assert all("Ukuleles" in item["category"] for item in payload["result"])
    # The model saw the tool output: second call history includes it.
    second_call_history = model.calls[1][0]
    assert any(message.role == "tool" for message in second_call_history)


def test_runaway_tool_loop_hits_fallback(agent_connection: sqlite3.Connection) -> None:
    model = FakeModel([_tool_call("get_store_info", {})] * 5)
    agent = Agent(model, agent_connection, max_tool_steps=2)
    assert agent.reply("onde fica a loja?") == FALLBACK_TEXT
    assert len(model.calls) == 2


def test_unknown_tool_error_feeds_back(agent_connection: sqlite3.Connection) -> None:
    model = FakeModel(
        [_tool_call("nope", {}), ChatResponse(content="Desculpe, tive um problema interno.")]
    )
    agent = Agent(model, agent_connection)
    assert agent.reply("oi") == "Desculpe, tive um problema interno."
    payload = json.loads(
        next(message for message in agent.history if message.role == "tool").content or "{}"
    )
    assert payload["ok"] is False


def test_last_tool_calls_records_turn_and_resets(agent_connection: sqlite3.Connection) -> None:
    model = FakeModel(
        [
            _tool_call("search_products", {"category": "ukuleles", "limit": 2}),
            ChatResponse(content="Achei!"),
            ChatResponse(content="De nada!"),
        ]
    )
    agent = Agent(model, agent_connection)
    assert agent.last_tool_calls == []
    agent.reply("quero um ukulele")
    assert len(agent.last_tool_calls) == 1
    entry = agent.last_tool_calls[0]
    assert entry["tool"] == "search_products"
    assert entry["arguments"] == {"category": "ukuleles", "limit": 2}
    assert json.loads(entry["result"])["ok"] is True
    # Next turn answers directly: record resets, no stale calls leak across turns.
    agent.reply("obrigado")
    assert agent.last_tool_calls == []
