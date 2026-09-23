"""Real keyboard/clipboard backend used outside of tests.

Typing arbitrary Japanese text via simulated key codes is unreliable because
it would require driving an IME. Instead we copy each character to the
clipboard and send the OS paste shortcut, which works uniformly for
hiragana, katakana, kanji, romaji and punctuation, into whatever
application/text field currently has focus.
"""
from __future__ import annotations

import sys
import time

import pyautogui
import pyperclip

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True  # move mouse to a screen corner to abort

_PASTE_MODIFIER = "command" if sys.platform == "darwin" else "ctrl"


def paste_char(ch: str) -> None:
    pyperclip.copy(ch)
    pyautogui.hotkey(_PASTE_MODIFIER, "v")


def backspace() -> None:
    pyautogui.press("backspace")


def countdown(seconds: int, on_tick=print) -> None:
    for remaining in range(seconds, 0, -1):
        on_tick(f"Starting in {remaining}... click into the target text field now.")
        time.sleep(1)


def run(text: str, config, stop_event=None, start_delay: int = 5, on_tick=print) -> None:
    """Restore the clipboard afterwards so we don't clobber the user's data."""
    from .core import human_type

    original_clipboard = None
    try:
        original_clipboard = pyperclip.paste()
    except Exception:
        pass

    countdown(start_delay, on_tick=on_tick)
    try:
        human_type(
            text,
            type_char=paste_char,
            backspace=backspace,
            sleep=time.sleep,
            config=config,
            stop_event=stop_event,
        )
    finally:
        if original_clipboard is not None:
            try:
                pyperclip.copy(original_clipboard)
            except Exception:
                pass
