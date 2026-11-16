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
import sys
import time

import pyautogui
import pyperclip

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True  # move mouse to a screen corner to abort

_PASTE_MODIFIER = "command" if sys.platform == "darwin" else "ctrl"

_BULLET_ACTIONS = {
    "toggle": lambda: pyautogui.hotkey("ctrl", "shift", "8"),
    "indent": lambda: pyautogui.press("tab"),
    "outdent": lambda: pyautogui.hotkey("shift", "tab"),
}


def paste_char(ch: str) -> None:
    pyperclip.copy(ch)
    pyautogui.hotkey(_PASTE_MODIFIER, "v")


def backspace() -> None:
    pyautogui.press("backspace")


def select_left(n: int) -> None:
    """Selects the n characters immediately before the cursor."""
    if n <= 0:
        return
    pyautogui.keyDown("shift")
    for _ in range(n):
        pyautogui.press("left")
    pyautogui.keyUp("shift")


def convert_to_kanji(n: int, surface: str) -> None:
    """Replaces the last `n` typed characters with `surface` in one atomic
    paste, so the hiragana reading visually turns into the kanji instead of
    being deleted character by character first."""
    select_left(n)
    paste_char(surface)


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
    bullet_mode: lines starting with "- ", "* " or "• " are turned
        into real Google Docs top-level bulleted-list items, and lines
        starting with "◦ " (optionally indented) become nested,
        second-level bullets, via Ctrl+Shift+8/Tab/Shift+Tab. Only enable
        this when typing into Google Docs -- those shortcuts do something
        else in other apps (e.g. Ctrl+Shift+8 toggles formatting marks in
        Word).
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
                convert_fn=convert_to_kanji,
            )
    finally:
        if original_clipboard is not None:
            try:
                pyperclip.copy(original_clipboard)
            except Exception:
                pass


def _run_with_bullets(text: str, config, reading_fn, stop_event) -> None:
    from .core import bullet_line_level, bullet_transition, human_type

    lines = text.split("\n")
    current_level = 0

    for idx, line in enumerate(lines):
        if stop_event is not None and stop_event.is_set():
            return

        target_level, content = bullet_line_level(line)
        for action in bullet_transition(current_level, target_level):
            _BULLET_ACTIONS[action]()
            time.sleep(0.15)
        current_level = target_level

        human_type(
            content,
            type_char=paste_char,
            backspace=backspace,
            sleep=time.sleep,
            config=config,
            stop_event=stop_event,
            reading_fn=reading_fn,
            convert_fn=convert_to_kanji,
        )

        if idx < len(lines) - 1:
            if stop_event is not None and stop_event.is_set():
                return
            pyautogui.press("enter")
            time.sleep(random.uniform(0.2, 0.6))
