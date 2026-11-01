"""Interactive CLI: chat with the Emporio da Musica agent in the terminal.

Builds the SQLite database at startup, opens one stateful :class:`Agent`, and
logs every turn as JSONL (one ``{"user", "assistant"}`` object per line) —
the raw source Phase 9 curates into ``examples/`` transcripts.
"""

import datetime
import json
import sys
from pathlib import Path
from typing import Any

from .agent import Agent
from .config import get_settings
from .data import connect, load_database
from .llm import get_chat_model
from .llm.base import LLMError

EXIT_WORDS = frozenset({"sair", "quit", "exit", "q"})


def append_turn(
    log_path: str | Path, user: str, assistant: str, tools: list[dict[str, Any]] | None = None
) -> None:
    """Append one conversation turn to the JSONL session log.

    ``tools`` is the agent's per-turn tool record (name, arguments, raw result)
    — empty when the model answered directly. Logged so live sessions stay
    X-rayable: road-vs-messenger diagnosis needs the road's actual output.
    """
    record = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "user": user,
        "assistant": assistant,
        "tools": list(tools) if tools else [],
    }
    path = Path(log_path)
    if path.parent != Path("."):
        path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_agent() -> tuple[Agent, str, int]:
    """Load settings, database and model; return agent, log path and row count."""
    settings = get_settings()
    counts = load_database(settings.database_path, settings.data_dir)
    total = sum(counts.values())
    model = get_chat_model(settings)
    agent = Agent(model, connect(settings.database_path), settings.max_tool_steps)
    return agent, settings.session_log_path, total


def main() -> None:
    """Run the REPL until the user quits (sair/quit/Ctrl+C/Ctrl+D)."""
    try:
        agent, log_path, total = build_agent()
    except (FileNotFoundError, LLMError, OSError) as exc:
        print(f"Não consegui iniciar (verifique .env e os CSVs em data/): {exc}")
        raise SystemExit(1) from exc

    provider = get_settings()
    model_name = provider.openai_model if provider.model_provider == "openai" else provider.ollama_model
    print(f"Empório da Música — {total} registros carregados (modelo: {model_name}).")
    print("Converse em português. Digite 'sair' para encerrar.\n")
    while True:
        try:
            user_text = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté logo! Sua música começa aqui. 🎶")
            break
        if not user_text:
            continue
        if user_text.lower() in EXIT_WORDS:
            print("Até logo! Sua música começa aqui. 🎶")
            break
        try:
            reply = agent.reply(user_text)
        except LLMError as exc:
            print(f"[técnico] modelo indisponível: {exc}", file=sys.stderr)
            reply = (
                "Tive uma instabilidade aqui no sistema. Pode repetir sua pergunta? "
                "Se preferir, chame a loja no WhatsApp (67) 3321-4500."
            )
        print(f"Loja: {reply}\n")
        append_turn(log_path, user_text, reply, agent.last_tool_calls)


if __name__ == "__main__":  # pragma: no cover - manual entry point
    main()
