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

    def test_structured_level_has_ten_questions(self) -> None:
        for level in (1, 2):
            state = self.store.create_session(topic="evaluation", category="facile", level=level)
            self._answer_session_perfectly(state)

        state = self.store.create_session(topic="evaluation", category="facile", level=3)
        self.assertEqual(state["total"], 10)
        self.assertEqual(state["category"], "facile")
        self.assertEqual(state["level"], 3)
        self.assertEqual(state["next_question"]["category"], "facile")
        self.assertEqual(state["next_question"]["level"], 3)

    def test_same_topic_does_not_repeat_between_levels(self) -> None:
        level_one = {
            q.question for q in self.bank.questions_for(topic="evaluation", category="facile", level=1)
        }
        level_two = {
            q.question for q in self.bank.questions_for(topic="evaluation", category="facile", level=2)
        }
        self.assertEqual(len(level_one), 10)
        self.assertEqual(len(level_two), 10)
        self.assertTrue(level_one.isdisjoint(level_two))

    def _answer_session_perfectly(self, state: dict) -> dict:
        while not state["completed"]:
            current_index = state["answered"]
            question = self.store._sessions[state["session_id"]]["questions"][current_index]
            state = self.store.answer(state["session_id"], question["correct_index"])
        return state

    def test_level_two_locked_until_level_one_perfect(self) -> None:
        with self.assertRaises(ValueError):
            self.store.create_session(topic="evaluation", category="facile", level=2)

        state = self.store.create_session(topic="evaluation", category="facile", level=1)
        current_index = state["answered"]
        question = self.store._sessions[state["session_id"]]["questions"][current_index]
        wrong_choice = 1 if question["correct_index"] == 0 else 0
        failed = self.store.answer(state["session_id"], wrong_choice)
        while not failed["completed"]:
            current_index = failed["answered"]
            question = self.store._sessions[failed["session_id"]]["questions"][current_index]
            failed = self.store.answer(failed["session_id"], question["correct_index"])

        with self.assertRaises(ValueError):
            self.store.create_session(topic="evaluation", category="facile", level=2)

        perfect = self.store.create_session(topic="evaluation", category="facile", level=1)
        self._answer_session_perfectly(perfect)

        unlocked = self.store.create_session(topic="evaluation", category="facile", level=2)
        self.assertEqual(unlocked["level"], 2)

    def test_next_category_locked_until_previous_category_completed(self) -> None:
        with self.assertRaises(ValueError):
            self.store.create_session(topic="evaluation", category="moyen", level=1)

        for level in range(1, 11):
            state = self.store.create_session(topic="evaluation", category="facile", level=level)
            self._answer_session_perfectly(state)

        unlocked = self.store.create_session(topic="evaluation", category="moyen", level=1)
        self.assertEqual(unlocked["category"], "moyen")

    def test_missing_session_raises(self) -> None:
        with self.assertRaises(KeyError):
            self.store.get("missing-session")

    def test_all_generated_questions_are_unique(self) -> None:
        texts = [q.question for q in self.bank.questions_for()]
        self.assertEqual(len(texts), len(set(texts)))

    def test_wrong_answer_returns_correct_choice_and_explanation(self) -> None:
        state = self.store.create_session(count=1, topic="evaluation")
        current = self.store.get(state["session_id"])
        question = current["next_question"]
        correct_index = self.store._sessions[state["session_id"]]["questions"][0]["correct_index"]
        wrong_choice = 1 if correct_index == 0 else 0

        result = self.store.answer(state["session_id"], wrong_choice)

        self.assertFalse(result["last_answer"]["is_correct"])
        self.assertEqual(result["last_answer"]["correct_choice"], question["choices"][correct_index])
        self.assertTrue(result["last_answer"]["explanation"])


if __name__ == "__main__":
    unittest.main()
