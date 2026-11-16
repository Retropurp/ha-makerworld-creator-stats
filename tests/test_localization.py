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
        catalog = (
            assignment_value(COMPONENT / "sensor.py", "SENSORS"),
            assignment_value(COMPONENT / "sensor.py", "DIAGNOSTIC_SENSORS"),
            assignment_value(COMPONENT / "rewards.py", "REWARD_SENSORS"),
            assignment_value(COMPONENT / "rewards.py", "CASH_SENSORS"),
        )
        expected = {key for group in catalog for key, *_ in group}
        expected.update(
            f"income_{kind}_{days}d" for kind in ("points", "money", "cash") for days in (7, 14, 30)
        )
        states = assignment_value(COMPONENT / "sensor.py", "CONNECTION_STATES")
        for translation in (self.en, self.de):
            sensors = translation["entity"]["sensor"]
            self.assertEqual(set(sensors), expected)
            self.assertEqual(set(sensors["connection_status"]["state"]), set(states))
            for key, data in sensors.items():
                self.assertTrue(data["name"].strip())
                if "beschreibung" in data.get("state_attributes", {}):
                    self.assertTrue(translation["common"][f"{key}_description"].strip())

    def test_form_error_and_abort_reasons_are_translated(self):
        expected = {
            "error": {"cannot_connect", "invalid_email", "invalid_code", "access_denied", "rate_limited", "cloudflare"},
            "abort": {"already_configured", "wrong_account", "reauth_successful"},
        }
        for locale in (self.en, self.de):
            for section, keys in expected.items():
                self.assertEqual(set(locale["config"][section]), keys)


if __name__ == "__main__":
    unittest.main()
