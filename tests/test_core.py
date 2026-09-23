import random
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from auto_typer.core import Config, human_type


class RecordingTyper:
    """Fake backend that reconstructs the final on-screen text."""

    def __init__(self):
        self.buffer = []
        self.type_calls = 0
        self.backspace_calls = 0

    def type_char(self, ch):
        self.buffer.append(ch)
        self.type_calls += 1

    def backspace(self):
        self.buffer.pop()
        self.backspace_calls += 1

    def result(self):
        return "".join(self.buffer)


class TestHumanType(unittest.TestCase):
    def test_no_typos_reproduces_text_exactly(self):
        text = "こんにちは、世界！"
        typer = RecordingTyper()
        cfg = Config(typo_rate=0.0, pause_rate=0.0)
        human_type(text, typer.type_char, typer.backspace, sleep=lambda s: None, config=cfg)
        self.assertEqual(typer.result(), text)
        self.assertEqual(typer.type_calls, len(text))
        self.assertEqual(typer.backspace_calls, 0)

    def test_with_typos_still_reproduces_text_exactly(self):
        text = "日本語のテキストを自動でタイプするテストです。長めの文章でtypoの発生も確認します。"
        for seed in range(25):
            typer = RecordingTyper()
            cfg = Config(typo_rate=0.5, transpose_share=0.3, pause_rate=0.2)
            rng = random.Random(seed)
            human_type(
                text,
                typer.type_char,
                typer.backspace,
                sleep=lambda s: None,
                config=cfg,
                rng=rng,
            )
            self.assertEqual(typer.result(), text, f"mismatch with seed {seed}")
            # a typo-heavy run should actually produce some backspaces
        self.assertGreater(typer.backspace_calls, 0)

    def test_sleep_is_called_and_varies(self):
        text = "あいうえお"
        delays = []
        typer = RecordingTyper()
        cfg = Config(typo_rate=0.0, pause_rate=0.0, cpm_min=100, cpm_max=1000)
        human_type(
            text,
            typer.type_char,
            typer.backspace,
            sleep=lambda s: delays.append(s),
            config=cfg,
            rng=random.Random(1),
        )
        self.assertEqual(len(delays), len(text))
        self.assertTrue(all(d > 0 for d in delays))
        # with a wide cpm range, delays shouldn't all be identical
        self.assertGreater(len(set(delays)), 1)

    def test_stop_event_halts_early(self):
        text = "あ" * 1000
        typer = RecordingTyper()
        stop_event = threading.Event()

        calls = {"n": 0}

        def sleep_and_stop(_):
            calls["n"] += 1
            if calls["n"] == 5:
                stop_event.set()

        human_type(
            text,
            typer.type_char,
            typer.backspace,
            sleep=sleep_and_stop,
            config=Config(typo_rate=0.0, pause_rate=0.0),
            stop_event=stop_event,
        )
        self.assertLess(typer.type_calls, len(text))

    def test_long_pause_after_punctuation(self):
        text = "そう。"
        delays = []
        typer = RecordingTyper()
        cfg = Config(typo_rate=0.0, pause_rate=0.0, long_pause_range=(2.0, 2.0))
        human_type(
            text,
            typer.type_char,
            typer.backspace,
            sleep=lambda s: delays.append(s),
            config=cfg,
            rng=random.Random(0),
        )
        # last char is "。" -> its char delay followed by a forced 2.0s long pause
        self.assertAlmostEqual(delays[-1], 2.0)


if __name__ == "__main__":
    unittest.main()
