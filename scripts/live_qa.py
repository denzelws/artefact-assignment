"""Live QA session: curated questions against a local Ollama model.

NOT a pytest file (name avoids the ``test_`` prefix on purpose): it needs a
running Ollama server and asserts nothing — a human judges the answers.
Deterministic behavior is covered by ``tests/test_agent.py`` (fake model).

Usage:
    .venv/bin/python scripts/live_qa.py
    EMPORIO_OLLAMA_MODEL=qwen2.5:7b .venv/bin/python scripts/live_qa.py

To add your own cases, append to ``MY_QUESTIONS`` below and re-run.
"""

import os

from emporio.agent import Agent
from emporio.config import Settings
from emporio.data import connect, load_database
from emporio.llm import get_chat_model

# ---------------------------------------------------------------------------
# Curated regression questions: one per critical path (products, money,
# policies). They run on a shared history, like a real conversation.
# ---------------------------------------------------------------------------
CURATED_QUESTIONS = [
    "Olá! Quais violões até R$ 1000 vocês têm?",
    "Meu pedido 8 chegou?",
    "Tem desconto no pix?",
    "Quero trocar um produto, como funciona?",
]

# ---------------------------------------------------------------------------
# ADD YOUR OWN QUESTIONS HERE. One string per line. Nasty cases welcome:
# typos ("qero um violao"), missing context ("e o frete?"), anger ("quero
# meu dinheiro de volta!"). If the answer invents facts, file it as a bug:
# note the question + wrong answer in plan.md section 10, then fix.
# ---------------------------------------------------------------------------
MY_QUESTIONS: list[str] = [
    "Ola, a loja de vcs vendem oq?"
]


def main() -> None:
    db_path = "/tmp/live_qa.sqlite"
    load_database(db_path, "data")
    model_name = os.environ.get("EMPORIO_OLLAMA_MODEL", "llama3.2:3b")
    print(f"Model: {model_name} | DB: {db_path}\n")
    agent = Agent(get_chat_model(Settings(ollama_model=model_name)), connect(db_path))

    for question in CURATED_QUESTIONS + MY_QUESTIONS:
        print("YOU:", question)
        print("AGENT:", agent.reply(question))
        print("-" * 60)


if __name__ == "__main__":
    main()
