"""
Tests for priority scoring engine: urgency, deadlines, user mentions, and transparent factors.
"""
import unittest
from core.priority_engine import PriorityEngine


class TestPriorityEngine(unittest.TestCase):
    def setUp(self):
        self.engine = PriorityEngine(user_name="Dev")

    def test_urgent_deadline_combination(self):
        text = "URGENT: The security compliance form must be submitted before 5 PM today."
        result = self.engine.evaluate_text(text, sender="Alex")
        self.assertEqual(result.level, "High")
        self.assertGreaterEqual(result.score, 65)
        self.assertTrue(any("urgency language" in r for r in result.reasons))
        self.assertTrue(any("immediate deadline" in r for r in result.reasons))

    def test_user_mention_boost(self):
        text = "Hey Dev, could you review the PR when free?"
        result = self.engine.evaluate_text(text, sender="Alex")
        self.assertTrue(any("mention of your name" in r for r in result.reasons))
        self.assertGreaterEqual(result.score, 35)

    def test_plan_change_detection(self):
        text = "Sprint sync has been rescheduled to tomorrow morning."
        result = self.engine.evaluate_text(text, sender="Maya")
        self.assertTrue(any("schedule/plan modification" in r for r in result.reasons))

    def test_routine_casual_message(self):
        text = "Tomorrow is pizza lunch at 12:30 PM!"
        engine_no_user = PriorityEngine(user_name=None)
        result = engine_no_user.evaluate_text(text, sender="Maya")
        self.assertIn(result.level, ["Medium", "Low"])

    def test_empty_text(self):
        result = self.engine.evaluate_text("", sender="")
        self.assertEqual(result.score, 0)
        self.assertEqual(result.level, "Low")


if __name__ == "__main__":
    unittest.main()
