"""Pause policy: restart persistence, escalation and hostile Retry-After."""

import unittest
from test_rewards import load

policy = load("backoff")


class BackoffTests(unittest.TestCase):
    def test_cloudflare_escalates_and_caps(self):
        state = policy.Backoff()
        for hours in (2, 4, 8, 12, 12, 12, 12):
            state.deny("cloudflare", 100000)
            self.assertEqual(state.remaining(100000), hours * 3600)

    def test_throttling_default_and_server_instruction(self):
        state = policy.Backoff()
        state.deny("throttled", 100000)
        self.assertEqual(state.remaining(100000), 1800)
        state.deny("throttled", 100000, retry_after=20000, jitter=30)
        self.assertEqual(state.remaining(100000), 20030)

    def test_jitter_cannot_exceed_daily_limit(self):
        state = policy.Backoff()
        state.deny("cloudflare", 100000, retry_after=86400, jitter=60)
        self.assertEqual(state.remaining(100000), 86400)

    def test_restore_preserves_deadline_and_failure_count(self):
        first = policy.Backoff()
        first.deny("cloudflare", 100000)
        restored = policy.Backoff()
        restored.restore(first.as_dict(), 101000)
        self.assertEqual(restored.remaining(101000), 6200)
        self.assertEqual(restored.strikes, 1)
        restored.deny("cloudflare", 108000)
        self.assertEqual(restored.remaining(108000), 14400)

    def test_success_resets_escalation(self):
        state = policy.Backoff()
        state.deny("cloudflare", 100000)
        state.reset()
        self.assertEqual(state.as_dict(), dict(until=0, strikes=0, reason=""))

    def test_invalid_cache_rejected(self):
        for change in ({"until": float("nan")}, {"until": True}, {"until": 9999999999}, {"strikes": True}, {"reason": "secret"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                policy.Backoff().restore(dict(until=100000, strikes=1, reason="cloudflare") | change, 100000)

    def test_retry_after_seconds_and_clamping(self):
        for value, expected in (("120", 120), ("999999999", 86400), ("-2", 0), ("NaN", 0), ("inf", 0), (None, 0), ("9" * 1000, 0)):
            self.assertEqual(policy.retry_after_seconds(value, 0), expected)

    def test_retry_after_http_date(self):
        self.assertEqual(policy.retry_after_seconds("Thu, 01 Jan 1970 01:00:00 GMT", 0), 3600)
        self.assertEqual(policy.retry_after_seconds("Thu, 01 Jan 1970 01:00:00 GMT", 7200), 0)


if __name__ == "__main__":
    unittest.main()
