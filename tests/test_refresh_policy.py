"""Offline regression tests for the low-traffic Beta 2 scheduling policy."""

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "custom_components" / "makerworld_creator_stats" / "refresh_policy.py"
SPEC = importlib.util.spec_from_file_location("refresh_policy", MODULE)
policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy)


class PolicyTests(unittest.TestCase):
    def test_initial_fetches_are_staggered(self):
        due = policy.first_due(10000)
        self.assertEqual(due["points"], 13600)
        self.assertEqual(due["boosts"], 17200)
        self.assertIsNone(policy.due_optional(due, 10000))
        self.assertEqual(policy.due_optional(due, 13600), "points")

    def test_only_one_extra_when_both_due(self):
        due = {"points": 100, "boosts": 200}
        self.assertEqual(policy.due_optional(due, 300), "points")
        due["points"] = 300 + policy.EXTRA_SECONDS
        self.assertEqual(policy.due_optional(due, 300), "boosts")

    def test_cache_requires_fresh_finite_timestamp(self):
        self.assertTrue(policy.valid_timestamp(100, 200))
        self.assertFalse(policy.valid_timestamp(201, 200))
        self.assertFalse(policy.valid_timestamp(True, 200))
        self.assertFalse(policy.valid_timestamp(float("nan"), 200))
        self.assertFalse(policy.valid_timestamp(1, 36000))

    def test_policy_intervals(self):
        self.assertEqual(policy.PROFILE_SECONDS, 3600)
        self.assertEqual(policy.EXTRA_SECONDS, 21600)
        self.assertEqual(policy.MAX_EXTRA_AGE, 28800)


if __name__ == "__main__":
    unittest.main()
