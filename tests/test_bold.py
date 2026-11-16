import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from auto_typer.core import Config, human_type_line, parse_bold_segments


class RecordingTyper:
    """Fake backend that reconstructs the final on-screen text and records
    where bold was toggled on/off."""

    def __init__(self):
        self.buffer = []
        self.bold_toggles = 0
        self.bold_spans = []  # list of (start_index, end_index) in buffer

    def type_char(self, ch):
        self.buffer.extend(ch)

    def backspace(self):
        self.buffer.pop()

    def bold_fn(self):
        self.bold_toggles += 1
        self.bold_spans.append(len(self.buffer))

    def result(self):
        return "".join(self.buffer)


class TestParseBoldSegments(unittest.TestCase):
    def test_no_markers(self):
        self.assertEqual(parse_bold_segments("plain text"), [("plain text", False)])

    def test_single_bold_span(self):
        self.assertEqual(
            parse_bold_segments("before **bold** after"),
            [("before ", False), ("bold", True), (" after", False)],
        )

    def test_whole_line_bold(self):
        self.assertEqual(parse_bold_segments("**第01場面**"), [("第01場面", True)])

    def test_multiple_bold_spans(self):
        self.assertEqual(
            parse_bold_segments("**一** middle **二**"),
            [("一", True), (" middle ", False), ("二", True)],
        )

    def test_empty_string(self):
        self.assertEqual(parse_bold_segments(""), [("", False)])


class TestHumanTypeLine(unittest.TestCase):
    def test_no_bold_fn_behaves_like_plain_typing(self):
        text = "こんにちは、世界"
        typer = RecordingTyper()
        cfg = Config(typo_rate=0.0, pause_rate=0.0)
        human_type_line(text, typer.type_char, typer.backspace, sleep=lambda s: None, config=cfg)
        self.assertEqual(typer.result(), text)
        self.assertEqual(typer.bold_toggles, 0)

    def test_no_markers_with_bold_fn_present_does_not_toggle(self):
        text = "こんにちは、世界"
        typer = RecordingTyper()
        cfg = Config(typo_rate=0.0, pause_rate=0.0)
        human_type_line(
            text, typer.type_char, typer.backspace, sleep=lambda s: None, config=cfg, bold_fn=typer.bold_fn
        )
        self.assertEqual(typer.result(), text)
        self.assertEqual(typer.bold_toggles, 0)

    def test_bold_span_is_wrapped_with_toggles(self):
        text = "前 **太字** 後"
        typer = RecordingTyper()
        cfg = Config(typo_rate=0.0, pause_rate=0.0)
        human_type_line(
            text, typer.type_char, typer.backspace, sleep=lambda s: None, config=cfg, bold_fn=typer.bold_fn
        )
        # markers removed, final visible text has no "**"
        self.assertEqual(typer.result(), "前 太字 後")
        self.assertEqual(typer.bold_toggles, 2)
        start, end = typer.bold_spans
        # toggled on right before "太字" was typed, off right after
        self.assertEqual(typer.result()[start:end], "太字")

    def test_multiple_bold_spans_each_wrapped(self):
        text = "**一** middle **二**"
        typer = RecordingTyper()
        cfg = Config(typo_rate=0.0, pause_rate=0.0)
        human_type_line(
            text, typer.type_char, typer.backspace, sleep=lambda s: None, config=cfg, bold_fn=typer.bold_fn
        )
        self.assertEqual(typer.result(), "一 middle 二")
        self.assertEqual(typer.bold_toggles, 4)


if __name__ == "__main__":
    unittest.main()
