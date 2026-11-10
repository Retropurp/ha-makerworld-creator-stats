"""Regression cases for rolling gross-income calculations."""

from datetime import datetime, timezone
import unittest

from test_rewards import load

transactions = load("transactions")


class TransactionTests(unittest.TestCase):
    def row(self, amount=5, regular=2, exclusive=3, date="2026-11-10T12:00:00Z"):
        return dict(pointTime=date, pointChange=amount, pointChangeRegular=regular, pointChangeExclusive=exclusive)

    def test_fractional_income(self):
        event = transactions.parse_transaction(self.row("5.25", "2.1", "3.15"))
        self.assertEqual(event["combined"], "5.25")
        self.assertEqual(event["exclusive"], "3.15")

    def test_expenses_do_not_reduce_income(self):
        event = transactions.parse_transaction(self.row(-524, -24, -500))
        self.assertEqual(event["combined"], "0")
        self.assertEqual(event["exclusive"], "0")

    def test_missing_split_remains_unknown(self):
        row = self.row()
        del row["pointChangeExclusive"]
        event = transactions.parse_transaction(row)
        self.assertIsNone(event["exclusive"])
        self.assertIsNone(transactions.income_in_window([event], "exclusive", 7, event["time"]))

    def test_naive_date_is_rejected(self):
        for date in ("2026-11-10T12:00:00", None, 123, "bad"):
            with self.assertRaises(transactions.TransactionError):
                transactions.parse_transaction(self.row(date=date))

    def test_invalid_amount(self):
        for value in (None, True, "nan", "Infinity", "bad"):
            with self.assertRaises(transactions.TransactionError):
                transactions.parse_transaction(self.row(amount=value))

    def test_rolling_boundaries_and_future(self):
        now = datetime(2026, 11, 10, 12, tzinfo=timezone.utc).timestamp()
        events = [
            transactions.parse_transaction(self.row(date="2026-11-03T12:00:00Z")),
            transactions.parse_transaction(self.row(date="2026-11-03T12:00:01Z")),
            transactions.parse_transaction(self.row(date="2026-11-10T12:00:00Z")),
            transactions.parse_transaction(self.row(date="2026-11-10T12:00:01Z")),
        ]
        self.assertEqual(transactions.income_in_window(events, "combined", 7, now), 10)
        self.assertEqual(transactions.income_in_window(events, "combined", 14, now), 15)

    def test_empty_history_is_zero(self):
        self.assertEqual(transactions.income_in_window([], "regular", 30, 100), 0)

    def test_cache_roundtrip(self):
        event = transactions.parse_transaction(self.row())
        timestamp = event["time"]
        synced, events = transactions.read_cache({"synced_at": timestamp, "events": [event]}, timestamp + 1)
        self.assertEqual(synced, timestamp)
        self.assertEqual(events, [event])

    def test_corrupt_cache(self):
        self.assertIsNone(transactions.read_cache(None, 100))
        self.assertIsNone(transactions.read_cache({"synced_at": 200, "events": []}, 100))
        self.assertIsNone(transactions.read_cache({"synced_at": 10, "events": [1]}, 100))
        self.assertIsNone(transactions.read_cache({"synced_at": 10, "events": [{"time": 1, "combined": "-1"}]}, 100))

    def test_cache_normalizes_timestamp(self):
        result = transactions.read_cache({"synced_at": 10, "events": [{"time": "1", "combined": "2"}]}, 100)
        self.assertEqual(result[1][0]["time"], 1.0)

    def test_history_interval_six_hours(self):
        self.assertEqual(transactions.HISTORY_INTERVAL, 21600)


if __name__ == "__main__":
    unittest.main()
