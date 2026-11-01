"""Shared text matching for store tools.

Same contract as the policy search: accent- and case-insensitive matching so
``violao`` finds ``Violão`` and ``TAKAMINE`` finds ``Takamine``.
"""

import re
import unicodedata


def normalize(text: str) -> str:
    """Lowercase, strip accents and punctuation; collapse to single spaces."""
    ascii_folded = "".join(
        char for char in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(char) != "Mn"
    )
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", ascii_folded)).strip()
