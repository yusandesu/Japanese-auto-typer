"""Real keyboard/clipboard backend used outside of tests.

Typing arbitrary Japanese text via simulated key codes is unreliable because
it would require driving an IME. Instead we copy each character (or, for a
converted kanji word, the whole word at once) to the clipboard and send the
OS paste shortcut, which works uniformly for hiragana, katakana, kanji,
romaji and punctuation, into whatever application/text field currently has
focus.
"""
from __future__ import annotations

import random
import re
import sys
import time

import pyautogui
import pyperclip

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True  # move mouse to a screen corner to abort

_PASTE_MODIFIER = "command" if sys.platform == "darwin" else "ctrl"

# Lines starting with one of these markers are treated as bullet items when
# bullet_mode is on. The marker itself is stripped before typing.
_BULLET_PREFIX_RE = re.compile(r"^[-*•]\s+")


def paste_char(ch: str) -> None:
    pyperclip.copy(ch)
    pyautogui.hotkey(_PASTE_MODIFIER, "v")


def backspace() -> None:
    pyautogui.press("backspace")


def countdown(seconds: int, on_tick=print) -> None:
    for remaining in range(seconds, 0, -1):
        on_tick(f"Starting in {remaining}... click into the target text field now.")
        time.sleep(1)


def _resolve_reading_fn(ime_mode: bool):
    if not ime_mode:
        return None
    from . import furigana

    if not furigana.available():
        return None
    return furigana.to_hiragana


def run(
    text: str,
    config,
    stop_event=None,
    start_delay: int = 5,
    on_tick=print,
    ime_mode: bool = False,
    bullet_mode: bool = False,
) -> None:
    """Type `text` into whatever window has focus.

    ime_mode: simulate typing kanji as its hiragana reading, then
        converting it (see auto_typer.core.human_type's reading_fn).
    bullet_mode: lines starting with "- ", "* " or "• " are turned into
        real Google Docs bulleted-list items via Ctrl+Shift+8. Only enable
        this when typing into Google Docs -- that shortcut does something
        else in other apps (e.g. toggles formatting marks in Word).
    """
    from .core import human_type

    reading_fn = _resolve_reading_fn(ime_mode)

    original_clipboard = None
    try:
        original_clipboard = pyperclip.paste()
    except Exception:
        pass

    countdown(start_delay, on_tick=on_tick)
    try:
        if bullet_mode:
            _run_with_bullets(text, config, reading_fn, stop_event)
        else:
            human_type(
                text,
                type_char=paste_char,
                backspace=backspace,
                sleep=time.sleep,
                config=config,
                stop_event=stop_event,
                reading_fn=reading_fn,
            )
    finally:
        if original_clipboard is not None:
            try:
                pyperclip.copy(original_clipboard)
            except Exception:
                pass


def _run_with_bullets(text: str, config, reading_fn, stop_event) -> None:
    from .core import human_type

    lines = text.split("\n")
    in_bullet = False

    for idx, line in enumerate(lines):
        if stop_event is not None and stop_event.is_set():
            return

        m = _BULLET_PREFIX_RE.match(line)
        is_bullet = bool(m)
        content = line[m.end():] if m else line

        if is_bullet != in_bullet:
            pyautogui.hotkey("ctrl", "shift", "8")
            time.sleep(0.15)
            in_bullet = is_bullet

        human_type(
            content,
            type_char=paste_char,
            backspace=backspace,
            sleep=time.sleep,
            config=config,
            stop_event=stop_event,
            reading_fn=reading_fn,
        )

        if idx < len(lines) - 1:
            if stop_event is not None and stop_event.is_set():
                return
            pyautogui.press("enter")
            time.sleep(random.uniform(0.2, 0.6))
