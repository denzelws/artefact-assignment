"""Shared Portuguese text matching for search (tools and policies).

One canonical home for the rules the live sessions forced us to learn:
- Accents/case/punctuation never matter (``violão`` == ``VIOLAO!``).
- Noun number never matters (``violoes`` == ``violão``) via :func:`stem`.
- Conversational residue never filters results: stopwords (``até``, ``de``),
  single letters (``R$`` -> ``r``) and pure numbers (``1000`` — prices belong
  to ``max_price``, not to text) are dropped by :func:`query_tokens`.
"""

import re
import unicodedata

STOPWORDS = frozenset(
    "a ao aos aquela aquelas aquela aquele aqueles aquilo as ate com como da das de do dos "
    "e em entre era eram esse essa esses essas este esta estes estas eu ele ela eles elas "
    "foi foram ha isso isto ja lhe lhes mas me meu minha meus minhas muito na nao nas nem "
    "no nos nosso nossa nossos nossas nunca o os ou para pela pelas pelo pelos por qual quais "
    "quando que quem se sem ser seu sua seus suas sob sobre sua suas tambem te tem tenho teu "
    "tua tuas um uma uns umas voce voces vos".split()
)


def normalize(text: str) -> str:
    """Lowercase, strip accents/punctuation; collapse to single spaces."""
    ascii_folded = "".join(
        char for char in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(char) != "Mn"
    )
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", ascii_folded)).strip()


def stem(token: str) -> str:
    """Reduce a Portuguese noun to its singular-ish base form.

    Handles the catalog's real cases (``violoes`` -> ``violao``,
    ``trocas`` -> ``troca``). Short tokens are left alone so words like
    ``tres`` or ``mais`` never become runaway substrings.
    """
    if token.endswith("oes") and len(token) > 4:
        return token[:-3] + "ao"
    if token.endswith("es") and len(token) > 4:
        return token[:-2]
    if token.endswith("s") and len(token) > 4:
        return token[:-1]
    return token


def query_tokens(text: str) -> list[str]:
    """Content-bearing stemmed tokens: drop stopwords, single chars, numbers."""
    return [
        stem(token)
        for token in normalize(text).split()
        if token and token not in STOPWORDS and len(token) > 1 and not token.isdigit()
    ]


def word_set(text: str) -> set[str]:
    """Stemmed whole words of a field, for set-membership scoring."""
    return {stem(word) for word in normalize(text).split() if word}
