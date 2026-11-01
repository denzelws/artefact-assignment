"""CLI session-log checks (the live REPL is exercised manually)."""

import json
from pathlib import Path

import pytest

from emporio import cli
from emporio.cli import append_turn, build_agent, main
from emporio.config import Settings
from emporio.llm.base import LLMError


def test_append_turn_writes_jsonl(tmp_path: Path) -> None:
    log = tmp_path / "sessions.jsonl"
    append_turn(log, "Oi", "Olá! Como posso ajudar?")
    append_turn(log, "Tchau", "Até logo!")
    lines = log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["user"] == "Oi"
    assert first["assistant"] == "Olá! Como posso ajudar?"
    assert "ts" in first


def test_append_turn_creates_parent_dirs(tmp_path: Path) -> None:
    log = tmp_path / "nested" / "dir" / "sessions.jsonl"
    append_turn(log, "Oi", "Olá!")
    assert log.is_file()


def test_append_turn_logs_tool_calls(tmp_path: Path) -> None:
    log = tmp_path / "sessions.jsonl"
    append_turn(log, "Oi", "Olá!", tools=[])
    tools = [{"tool": "search_products", "arguments": {"query": "Tagima"}, "result": "{}"}]
    append_turn(log, "Tagima", "Achei!", tools=tools)
    lines = log.read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0])["tools"] == []
    assert json.loads(lines[1])["tools"] == tools


class StubAgent:
    """Minimal Agent double: canned reply plus a visible tool record."""

    def __init__(self, replies: list[str], tools=None, fail: bool = False) -> None:  # type: ignore[no-untyped-def]
        self.replies = list(replies)
        self.last_tool_calls = tools or []
        self.fail = fail

    def reply(self, user_text: str) -> str:
        if self.fail:
            raise LLMError("model down")
        return self.replies.pop(0)


def _scripted_input(monkeypatch: pytest.MonkeyPatch, lines: list[str]) -> None:
    answers = iter(lines)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))


def _stub_settings(tmp_path: Path) -> Settings:
    return Settings(
        database_path=str(tmp_path / "cli.sqlite"),
        data_dir="data",
        session_log_path=str(tmp_path / "sessions.jsonl"),
    )


def test_build_agent_loads_database(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(cli, "get_chat_model", lambda settings: object())
    monkeypatch.setattr(cli, "get_settings", lambda: _stub_settings(tmp_path))
    agent, log_path, total = build_agent()
    try:
        assert total == 191
        assert log_path == str(tmp_path / "sessions.jsonl")
    finally:
        agent.connection.close()


def test_main_startup_failure_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "build_agent", lambda: (_ for _ in ()).throw(FileNotFoundError("no csv")))
    with pytest.raises(SystemExit):
        main()


def test_main_repl_logs_turn_and_exits(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    log = tmp_path / "sessions.jsonl"
    tools = [{"tool": "search_products", "arguments": {}, "result": "{}"}]
    agent = StubAgent(["Olá!"], tools=tools)
    monkeypatch.setattr(cli, "build_agent", lambda: (agent, str(log), 191))
    _scripted_input(monkeypatch, ["Oi", "sair"])
    main()
    lines = log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert (record["user"], record["assistant"], record["tools"]) == ("Oi", "Olá!", tools)


def test_main_model_error_logs_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    log = tmp_path / "sessions.jsonl"
    agent = StubAgent([], fail=True)
    monkeypatch.setattr(cli, "build_agent", lambda: (agent, str(log), 191))
    _scripted_input(monkeypatch, ["Oi", "sair"])
    main()
    record = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
    assert "instabilidade" in record["assistant"]
    assert record["tools"] == []


def test_main_eof_exits_without_logging(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    log = tmp_path / "sessions.jsonl"
    agent = StubAgent(["nunca"], tools=[])
    monkeypatch.setattr(cli, "build_agent", lambda: (agent, str(log), 191))

    def raise_eof(_prompt: str = "") -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)
    main()
    assert not log.is_file()


def test_main_blank_input_skipped(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    log = tmp_path / "sessions.jsonl"
    agent = StubAgent(["Olá!"], tools=[])
    monkeypatch.setattr(cli, "build_agent", lambda: (agent, str(log), 191))
    _scripted_input(monkeypatch, ["   ", "Oi", "sair"])
    main()
    lines = log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["user"] == "Oi"
