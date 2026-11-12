"""Regression checks for localization keys and existing sensor identity.

Runs without Home Assistant or MakerWorld credentials.
"""

import ast
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "makerworld_creator_stats"


def assignment_value(path, name):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for statement in tree.body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in statement.targets
        ):
            return ast.literal_eval(statement.value)
    raise AssertionError(f"Missing assignment {name} in {path}")


def shape(value):
    if isinstance(value, dict):
        return {key: shape(item) for key, item in value.items()}
    return type(value).__name__


class LocalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
        cls.en = json.loads((COMPONENT / "translations" / "en.json").read_text(encoding="utf-8"))
        cls.de = json.loads((COMPONENT / "translations" / "de.json").read_text(encoding="utf-8"))

    def test_translations_have_matching_shapes(self):
        self.assertEqual(shape(self.source), shape(self.en))
        self.assertEqual(shape(self.source), shape(self.de))
        self.assertEqual(self.source, self.en)

    def test_english_default_and_title(self):
        self.assertEqual(self.source["title"], "MakerWorld Creator Stats")
        self.assertEqual(self.source["config"]["step"]["user"]["title"], "Sign in to MakerWorld")
        self.assertEqual(self.de["config"]["step"]["user"]["title"], "MakerWorld anmelden")

    def test_placeholder_names_are_preserved(self):
        for data in (self.source, self.en, self.de):
            self.assertIn("{detail}", data["config"]["error"]["cannot_connect"])

    def test_select_options_are_localized_and_use_stable_values(self):
        cases = {
            "sensor_view": ("presentation.py", "VIEWS"),
            "shop_region": ("rewards.py", "REGIONS"),
            "points_basis": ("rewards.py", "BASES"),
        }
        config_source = (COMPONENT / "config_flow.py").read_text(encoding="utf-8")
        for selector_key, (filename, assignment) in cases.items():
            with self.subTest(selector=selector_key):
                allowed = assignment_value(COMPONENT / filename, assignment)
                for translation in (self.source, self.de):
                    localized = translation["selector"][selector_key]["options"]
                    self.assertEqual(set(localized), set(allowed))
                self.assertIn(f'translation_key="{selector_key}"', config_source)

    def test_sensor_translations_match_registered_keys(self):
        raw = assignment_value(COMPONENT / "sensor.py", "SENSORS")
        gifts = assignment_value(COMPONENT / "rewards.py", "REWARD_SENSORS")
        cash = assignment_value(COMPONENT / "rewards.py", "CASH_SENSORS")
        self.assertEqual(len(raw), 25)
        self.assertEqual(len(gifts), 6)
        self.assertEqual(len(cash), 6)

        expected = {item[0] for item in (*raw, *gifts, *cash)}
        for days in (7, 14, 30):
            expected.add(f"income_money_{days}d")
            expected.add(f"income_cash_{days}d")
            for basis in ("regular", "combined", "exclusive"):
                expected.add(f"income_points_{days}d_{basis}")

        self.assertEqual(len(expected), 52)
        for translation in (self.source, self.en, self.de):
            keys = set(translation["entity"]["sensor"])
            self.assertEqual(keys, expected)
            for key in keys:
                self.assertTrue(translation["entity"]["sensor"][key]["name"].strip())

    def test_unique_id_contract_remains_unchanged(self):
        source = (COMPONENT / "sensor.py").read_text(encoding="utf-8")
        self.assertIn('f"{coordinator.account_id}_{description.key}"', source)
        self.assertIn('f"income_{kind}_{days}d"', source)
        self.assertIn("translation_key=translation_key or key", source)


if __name__ == "__main__":
    unittest.main()
