"""Backend-agnostic human-like typing simulation.

This module contains no OS/keyboard dependencies so it can be unit tested
without a display. A backend (see backend.py) supplies the actual
``type_char`` / ``backspace`` functions that hit the keyboard.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class Config:
    # Typing speed, expressed as characters-per-minute range. A new random
    # value in this range is picked for every character to avoid a robotic,
    # perfectly even cadence.
    cpm_min: int = 180
    cpm_max: int = 340

    # Probability that any given character is preceded by a mistake.
    typo_rate: float = 0.04
    # Of the typos made, the fraction that are a single wrong character
    # (typed then corrected) vs. a transposition of two adjacent characters.
    transpose_share: float = 0.3
    # Pool of characters used to generate a "wrong key" typo. Mixed hiragana
    # + common punctuation keeps it plausible for any Japanese text.
    typo_pool: str = (
        "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほ"
        "まみむめもやゆよらりるれろわをんっーゃゅょ、。"
    )
    # How long the "typist" takes to notice and correct a typo.
    reaction_delay_range: tuple[float, float] = (0.08, 0.28)

    # Random "thinking" pauses unrelated to typos.
    pause_rate: float = 0.03
    pause_range: tuple[float, float] = (0.3, 1.2)

    # Longer, more deliberate pauses after sentence-ending punctuation.
    long_pause_chars: frozenset[str] = field(
        default_factory=lambda: frozenset("。、!?!?\n")
    )
    long_pause_range: tuple[float, float] = (0.35, 1.1)

    def char_delay(self, rng: random.Random) -> float:
        cpm = rng.uniform(self.cpm_min, self.cpm_max)
        chars_per_second = cpm / 60.0
        return 1.0 / chars_per_second


def human_type(
    text: str,
    type_char,
    backspace,
    sleep,
    config: Config | None = None,
    rng: random.Random | None = None,
    stop_event=None,
) -> None:
    """Type ``text`` character by character with human-like timing.

    Parameters
    ----------
    type_char: callable(str) -> None
        Emits a single character (a backend paste/keystroke call).
    backspace: callable() -> None
        Deletes the previously typed character.
    sleep: callable(float) -> None
        Sleeps for the given number of seconds (injected for testability).
    stop_event: object with ``is_set()`` -> bool, optional
        Checked between characters to allow cancellation.
    """
    cfg = config or Config()
    rnd = rng or random.Random()

    i = 0
    n = len(text)
    while i < n:
        if stop_event is not None and stop_event.is_set():
            return

        ch = text[i]

        made_typo = rnd.random() < cfg.typo_rate
        if made_typo and rnd.random() < cfg.transpose_share and i + 1 < n:
            # Transposition typo: type the next two characters swapped,
            # notice, delete both, then type them in the correct order.
            next_ch = text[i + 1]
            type_char(next_ch)
            sleep(cfg.char_delay(rnd))
            type_char(ch)
            sleep(rnd.uniform(*cfg.reaction_delay_range))
            backspace()
            sleep(rnd.uniform(*cfg.reaction_delay_range) / 2)
            backspace()
            sleep(rnd.uniform(*cfg.reaction_delay_range) / 2)
            type_char(ch)
            sleep(cfg.char_delay(rnd))
            type_char(next_ch)
            i += 2
        elif made_typo:
            # Wrong-character typo: type a plausible wrong char, notice it,
            # backspace, then type the correct one.
            wrong = rnd.choice(cfg.typo_pool)
            if wrong == ch and len(cfg.typo_pool) > 1:
                # avoid a no-op "typo" that happens to match
                alt_pool = cfg.typo_pool.replace(ch, "")
                wrong = rnd.choice(alt_pool) if alt_pool else wrong
            type_char(wrong)
            sleep(rnd.uniform(*cfg.reaction_delay_range))
            backspace()
            sleep(rnd.uniform(*cfg.reaction_delay_range) / 2)
            type_char(ch)
            i += 1
        else:
            type_char(ch)
            i += 1

        sleep(cfg.char_delay(rnd))

        if ch in cfg.long_pause_chars:
            sleep(rnd.uniform(*cfg.long_pause_range))
        elif rnd.random() < cfg.pause_rate:
            sleep(rnd.uniform(*cfg.pause_range))
