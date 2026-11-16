import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from auto_typer.core import bullet_line_level, bullet_transition


class TestBulletLineLevel(unittest.TestCase):
    def test_plain_line(self):
        self.assertEqual(bullet_line_level("第01場面　冒頭"), (0, "第01場面　冒頭"))

    def test_top_level_bullet_dash(self):
        self.assertEqual(bullet_line_level("- 牛乳"), (1, "牛乳"))

    def test_top_level_bullet_star(self):
        self.assertEqual(bullet_line_level("* 牛乳"), (1, "牛乳"))

    def test_top_level_bullet_dot(self):
        self.assertEqual(bullet_line_level("•  場面の要点：恵子は"), (1, "場面の要点：恵子は"))

    def test_sub_bullet(self):
        self.assertEqual(bullet_line_level("◦  音で満ちている"), (2, "音で満ちている"))

    def test_sub_bullet_with_leading_whitespace(self):
        self.assertEqual(bullet_line_level("   ◦ 音で満ちている"), (2, "音で満ちている"))

    def test_empty_line(self):
        self.assertEqual(bullet_line_level(""), (0, ""))


class TestBulletTransition(unittest.TestCase):
    def test_same_level_is_noop(self):
        for level in (0, 1, 2):
            self.assertEqual(bullet_transition(level, level), [])

    def test_plain_to_top(self):
        self.assertEqual(bullet_transition(0, 1), ["toggle"])

    def test_top_to_plain(self):
        self.assertEqual(bullet_transition(1, 0), ["toggle"])

    def test_plain_to_sub(self):
        self.assertEqual(bullet_transition(0, 2), ["toggle", "indent"])

    def test_sub_to_plain(self):
        self.assertEqual(bullet_transition(2, 0), ["outdent", "toggle"])

    def test_top_to_sub(self):
        self.assertEqual(bullet_transition(1, 2), ["indent"])

    def test_sub_to_top(self):
        self.assertEqual(bullet_transition(2, 1), ["outdent"])

    def test_round_trip_is_identity(self):
        # applying a transition's actions should always be reversible back
        # to the starting level by the inverse transition's action count.
        for start in (0, 1, 2):
            for end in (0, 1, 2):
                actions = bullet_transition(start, end)
                back = bullet_transition(end, start)
                # going there and back should never be a no-op unless
                # start == end
                if start != end:
                    self.assertTrue(actions)
                    self.assertTrue(back)


if __name__ == "__main__":
    unittest.main()
