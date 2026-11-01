"""CLI session-log checks (the REPL itself is exercised manually)."""

import json
from pathlib import Path

from emporio.cli import append_turn


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
