"""Regional gift-card estimates based on explicitly selected terms."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

SOURCE = "https://forum.bambulab.com/t/live-stats-app-for-makerworld-models-analytics/246976/40"
SOURCE_DATE = "2026-04-10"
# Community reports. Availability and current shop terms require confirmation.
PRESETS = {
    "us": ("USD", 40, 490),
    "eu": ("EUR", 40, 524),
    "uk": ("GBP", 35, 535),
    "ca": ("CAD", 55, 504),
    "au": ("AUD", 65, 511),
    "jp": ("JPY", 5300, 502),
    "asia": ("USD", 40, 490),
    "kr": ("KRW", 58000, 490),
}
REGIONS = {
    "unset": "Bitte Shop wählen",
    "eu": "EU · EUR · experimentell",
    "us": "USA · USD · experimentell",
    "uk": "Vereinigtes Königreich · GBP · experimentell",
    "ca": "Kanada · CAD · experimentell",
    "au": "Australien · AUD · experimentell",
    "jp": "Japan · JPY · experimentell",
    "asia": "ASIA laut Forum · USD · experimentell, Währung prüfen",
    "kr": "Südkorea · KRW · experimentell",
    "cn": "China · kein Guthaben-Angebot in der Quelle belegt",
    "custom": "Benutzerdefiniert",
}
BASES = {"regular": "Nur reguläre Punkte", "combined": "Reguläre und exklusive Punkte"}
REWARD_SENSORS = (
    ("reward_balance_value", "Punktekonto Gutschein-Gegenwert", "mdi:cash", "money"),
    ("reward_earned_value", "Verdiente Punkte Gutschein-Gegenwert", "mdi:cash-plus", "money"),
    ("reward_cards", "Rechnerisch finanzierbare Gutscheine", "mdi:ticket", "count"),
    ("reward_credit", "Rechnerisch finanzierbares Guthaben", "mdi:gift", "money"),
    ("reward_missing", "Punkte bis zum nächsten Gutschein", "mdi:target", "points"),
    ("reward_progress", "Fortschritt zum nächsten Gutschein", "mdi:progress-clock", "percent"),
)


def number(value):
    """Convert valid API values and settings without losing threshold precision."""
    if value is None or isinstance(value, bool):
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return result if result.is_finite() and result >= 0 else None


def reward_values(profile, options):
    """Compute estimates only with a selected shop and complete point inputs."""
    if options.get("shop_region", "unset") not in (*PRESETS, "custom"):
        return {}
    cost = number(options.get("card_points"))
    face = number(options.get("card_value"))
    currency = options.get("currency", "")
    if not cost or not face or len(currency) != 3 or not currency.isascii() or not currency.isalpha():
        return {}
    if options.get("points_basis", "regular") == "combined":
        balance = number(profile.points)
        earned = number(profile.points_income_total)
        if earned is None:
            regular = number(profile.points_earned)
            exclusive = number(profile.points_earned_exclusive)
            if regular is not None and exclusive is not None:
                earned = regular + exclusive
    else:
        balance = number(profile.points_regular)
        earned = number(profile.points_earned)
    digits = Decimal("1") if currency.upper() in ("JPY", "KRW") else Decimal("0.01")

    def money(points):
        return float((points * face / cost).quantize(digits, rounding=ROUND_HALF_UP))

    result = {}
    if earned is not None:
        result["reward_earned_value"] = money(earned)
    if balance is not None:
        cards = int(balance // cost)
        remainder = balance % cost
        result.update(
            reward_balance_value=money(balance),
            reward_cards=cards,
            reward_credit=float(Decimal(cards) * face),
            reward_missing=float(cost - remainder),
            reward_progress=float(remainder / cost * 100),
        )
    return result
