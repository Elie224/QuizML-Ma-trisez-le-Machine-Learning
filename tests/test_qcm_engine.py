import unittest

from qcm_engine_fr import QcmSessionStore, QuestionBank


class QcmEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bank = QuestionBank()
        self.store = QcmSessionStore(self.bank)

    def test_create_session_and_answer_flow(self) -> None:
        state = self.store.create_session(count=3)
        self.assertFalse(state["completed"])
        self.assertEqual(state["answered"], 0)
        self.assertEqual(state["total"], 3)

        for _ in range(3):
            current = self.store.get(state["session_id"])
            self.assertIsNotNone(current["next_question"])
            # Always answer with choice 0 for deterministic test behavior.
            state = self.store.answer(state["session_id"], 0)

        self.assertTrue(state["completed"])
        self.assertEqual(state["answered"], 3)
        self.assertGreaterEqual(state["score"], 0)
        self.assertLessEqual(state["score"], 3)

    def test_topic_filter(self) -> None:
        state = self.store.create_session(count=2, topic="evaluation")
        q = state["next_question"]
        self.assertEqual(q["topic"], "evaluation")

    def test_structured_level_has_twenty_questions(self) -> None:
        state = self.store.create_session(topic="evaluation", category="facile", level=3)
        self.assertEqual(state["total"], 20)
        self.assertEqual(state["category"], "facile")
        self.assertEqual(state["level"], 3)
        self.assertEqual(state["next_question"]["category"], "facile")
        self.assertEqual(state["next_question"]["level"], 3)

    def test_missing_session_raises(self) -> None:
        with self.assertRaises(KeyError):
            self.store.get("missing-session")

    def test_all_generated_questions_are_unique(self) -> None:
        texts = [q.question for q in self.bank.questions_for()]
        self.assertEqual(len(texts), len(set(texts)))


if __name__ == "__main__":
    unittest.main()
