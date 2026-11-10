"""Gift-card arithmetic regressions, runnable without Home Assistant."""

import importlib.util
from pathlib import Path
import sys
import unittest

COMPONENT = Path(__file__).resolve().parents[1] / "custom_components/makerworld_creator_stats"


def load(name):
    spec = importlib.util.spec_from_file_location(name, COMPONENT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


profile = load("profile")
rewards = load("rewards")


class RewardTests(unittest.TestCase):
    def setUp(self):
        self.options = dict(shop_region="eu", currency="EUR", card_value="40", card_points="524", points_basis="regular")

    def values(self, balance, **kwargs):
        return rewards.reward_values(profile.MakerWorldProfile(points_reported=balance, **kwargs), self.options)

    def test_example(self):
        values = self.values(800)
        self.assertEqual(values["reward_balance_value"], 61.07)
        self.assertEqual(values["reward_cards"], 1)
        self.assertEqual(values["reward_credit"], 40)
        self.assertEqual(values["reward_missing"], 248)

    def test_exact_threshold_targets_the_following_card(self):
        for balance, cards in ((0, 0), (524, 1), (1048, 2)):
            values = self.values(balance)
            self.assertEqual(values["reward_cards"], cards)
            self.assertEqual(values["reward_progress"], 0)
            self.assertEqual(values["reward_missing"], 524)

    def test_fraction_just_below_threshold(self):
        values = self.values("523.999999")
        self.assertEqual(values["reward_cards"], 0)
        self.assertEqual(values["reward_missing"], 0.000001)

    def test_combined_basis(self):
        self.options["points_basis"] = "combined"
        values = self.values(22, points_reported_exclusive=522.547, points_total_reported=544.547, points_income_total=15182.547)
        self.assertEqual(values["reward_cards"], 1)
        self.assertEqual(values["reward_balance_value"], 41.57)
        self.assertEqual(values["reward_earned_value"], 1158.97)

    def test_lifetime_regular_basis(self):
        values = self.values(22, points_earned=4036, points_income_total=15182)
        self.assertEqual(values["reward_earned_value"], 308.09)

    def test_missing_balance_keeps_earned_value(self):
        values = self.values(None, points_earned=524)
        self.assertEqual(values, {"reward_earned_value": 40})

    def test_missing_earned_keeps_balance(self):
        self.assertNotIn("reward_earned_value", self.values(524))

    def test_combined_partial_earned_is_unavailable(self):
        self.options["points_basis"] = "combined"
        self.assertNotIn("reward_earned_value", self.values(1, points_earned=524))

    def test_combined_earned_fallback(self):
        self.options["points_basis"] = "combined"
        values = self.values(1, points_earned=500, points_earned_exclusive=24)
        self.assertEqual(values["reward_earned_value"], 40)

    def test_no_shop_and_china(self):
        for region in ("unset", "cn", "unknown"):
            self.options["shop_region"] = region
            self.assertEqual(self.values(524), {})
        self.assertEqual(rewards.reward_values(profile.MakerWorldProfile(), {}), {})

    def test_all_regional_thresholds(self):
        for region, (currency, value, points) in rewards.PRESETS.items():
            self.options.update(shop_region=region, currency=currency, card_value=value, card_points=points)
            result = self.values(points)
            self.assertEqual(result["reward_cards"], 1)
            self.assertEqual(result["reward_balance_value"], value)

    def test_custom_rate(self):
        self.options.update(shop_region="custom", currency="GBP", card_value="10", card_points="100")
        self.assertEqual(self.values(250)["reward_balance_value"], 25)

    def test_invalid_rates(self):
        for field in ("card_value", "card_points"):
            for value in (0, -1, True, None, "nan", "Infinity", "bad"):
                options = self.options | {field: value}
                self.assertEqual(rewards.reward_values(profile.MakerWorldProfile(points_reported=524), options), {})

    def test_invalid_points(self):
        for value in (-1, True, float("inf"), "nan", "bad"):
            self.assertEqual(self.values(value), {})


if __name__ == "__main__":
    unittest.main()
