import tempfile
import unittest
from pathlib import Path

import qcm_leaderboard_fr as lb


class QcmLeaderboardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.old_path = lb.LEADERBOARD_PATH
        lb.LEADERBOARD_PATH = Path(self.tmp.name) / "leaderboard.json"

    def tearDown(self) -> None:
        lb.LEADERBOARD_PATH = self.old_path
        self.tmp.cleanup()

    def test_submit_and_sort(self) -> None:
        lb.submit_score("alice", 3, 5)
        lb.submit_score("bob", 5, 5)
        lb.submit_score("carol", 4, 5)

        top = lb.top(limit=3)
        self.assertEqual(len(top), 3)
        self.assertEqual(top[0]["player"], "bob")
        self.assertEqual(top[1]["player"], "carol")
        self.assertEqual(top[2]["player"], "alice")

    def test_submit_normalizes_values(self) -> None:
        item = lb.submit_score("", -2, 0)
        self.assertEqual(item["player"], "joueur")
        self.assertEqual(item["score"], 0)
        self.assertEqual(item["total"], 1)

    def test_csv_export_contains_header_and_rows(self) -> None:
        lb.submit_score("alice", 3, 5)
        csv_text = lb.to_csv(limit=10)
        self.assertIn("rank,player,score,total,ratio,submitted_at", csv_text)
        self.assertIn("alice", csv_text)


if __name__ == "__main__":
    unittest.main()
