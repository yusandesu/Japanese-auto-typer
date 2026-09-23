"""Command-line entry point, for scripting or headless-ish use.

Example:
    python main.py --cli --file message.txt --cpm-min 200 --cpm-max 350 --delay 5
"""
from __future__ import annotations

import argparse
import sys
import threading

from .core import Config


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Type text like a human, into whatever window has focus.")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="Path to a text file to type.")
    src.add_argument("--stdin", action="store_true", help="Read text to type from stdin.")
    p.add_argument("--cpm-min", type=int, default=180, help="Minimum characters/minute.")
    p.add_argument("--cpm-max", type=int, default=340, help="Maximum characters/minute.")
    p.add_argument("--typo-rate", type=float, default=0.04, help="Probability (0-1) of a typo per char.")
    p.add_argument("--pause-rate", type=float, default=0.03, help="Probability (0-1) of a random pause per char.")
    p.add_argument("--delay", type=int, default=5, help="Seconds to wait before typing starts.")
    p.add_argument(
        "--ime",
        action="store_true",
        default=True,
        help="Type kanji as its hiragana reading, then convert (default: on, needs pykakasi).",
    )
    p.add_argument(
        "--no-ime",
        action="store_false",
        dest="ime",
        help="Disable hiragana-then-convert simulation; type kanji directly.",
    )
    p.add_argument(
        "--bullets",
        action="store_true",
        help='Treat lines starting with "- " or "* " as Google Docs bullets '
        "(sends Ctrl+Shift+8 -- only use this when typing into Google Docs).",
    )
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.stdin:
        text = sys.stdin.read()
    else:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()

    config = Config(
        cpm_min=args.cpm_min,
        cpm_max=args.cpm_max,
        typo_rate=args.typo_rate,
        pause_rate=args.pause_rate,
    )

    from . import backend

    stop_event = threading.Event()
    try:
        backend.run(
            text,
            config,
            stop_event=stop_event,
            start_delay=args.delay,
            ime_mode=args.ime,
            bullet_mode=args.bullets,
        )
    except KeyboardInterrupt:
        stop_event.set()
        print("\nStopped.")


if __name__ == "__main__":
    main()
