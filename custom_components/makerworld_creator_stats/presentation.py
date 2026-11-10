"""Sensor groups selected by the user in the options dialog."""

VIEWS = {
    "both": "Gutscheine und USD-Auszahlung",
    "gifts": "Nur Guthaben-Gutscheine",
    "cash": "Nur direkte USD-Auszahlung",
}


def sensor_group(key):
    if key.startswith(("reward_", "income_money_")):
        return "gifts"
    if key.startswith(("cash_", "income_cash_")):
        return "cash"
    return None


def show_sensor(key, options):
    view = options.get("sensor_view", "both")
    return view not in ("gifts", "cash") or sensor_group(key) in (None, view)
