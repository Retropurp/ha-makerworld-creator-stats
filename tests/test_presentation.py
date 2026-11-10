"""Sensor selection for new and existing installations."""

import unittest

from test_rewards import load

presentation = load("presentation")
rewards = load("rewards")


class PresentationTests(unittest.TestCase):
    def test_legacy_install_keeps_both(self):
        for key, *_ in (*rewards.REWARD_SENSORS, *rewards.CASH_SENSORS):
            self.assertTrue(presentation.show_sensor(key, {}))

    def test_general_sensors_always_selected(self):
        for view in presentation.VIEWS:
            for key in ("points", "points_exclusive", "income_points_7d", "likes"):
                self.assertTrue(presentation.show_sensor(key, {"sensor_view": view}))

    def test_gift_selection(self):
        for key, *_ in rewards.REWARD_SENSORS:
            self.assertTrue(presentation.show_sensor(key, {"sensor_view": "gifts"}))
        for key, *_ in rewards.CASH_SENSORS:
            self.assertFalse(presentation.show_sensor(key, {"sensor_view": "gifts"}))

    def test_cash_selection(self):
        for key, *_ in rewards.CASH_SENSORS:
            self.assertTrue(presentation.show_sensor(key, {"sensor_view": "cash"}))
        for key, *_ in rewards.REWARD_SENSORS:
            self.assertFalse(presentation.show_sensor(key, {"sensor_view": "cash"}))

    def test_period_values_follow_selection(self):
        for days in (7, 14, 30):
            for view in ("cash", "gifts"):
                self.assertEqual(presentation.show_sensor(f"income_cash_{days}d", {"sensor_view": view}), view == "cash")
                self.assertEqual(presentation.show_sensor(f"income_money_{days}d", {"sensor_view": view}), view == "gifts")

    def test_unknown_view_is_backward_compatible(self):
        self.assertTrue(presentation.show_sensor("cash_claimable", {"sensor_view": "unknown"}))


if __name__ == "__main__":
    unittest.main()
