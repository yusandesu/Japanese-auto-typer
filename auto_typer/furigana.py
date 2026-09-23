"""Kanji -> hiragana reading lookup.

Used to simulate typing a word's reading first and then converting it to
kanji, the way a real Japanese IME works. Backed by pykakasi, which needs
no external dictionary download and is pure Python.
"""
from __future__ import annotations

try:
    import pykakasi

    _kks = pykakasi.kakasi()
except Exception:  # pykakasi not installed, or failed to initialize
    _kks = None


def available() -> bool:
    return _kks is not None


def to_hiragana(text: str) -> str:
    """Best-effort hiragana reading of `text` (assumed to be kanji).

    Falls back to returning `text` unchanged if pykakasi isn't available
    or conversion fails for any reason.
    """
    if _kks is None:
        return text
    try:
        return "".join(item["hira"] for item in _kks.convert(text))
    except Exception:
        return text
