"""All account statistics exposed as individual sensors."""

from decimal import Decimal, ROUND_DOWN
import time

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .profile import MakerWorldProfile
from .transactions import HISTORY_INTERVAL, income_in_window
from .presentation import sensor_group, show_sensor
from .rewards import (
    CASH_MAX, CASH_MIN, CASH_RATE, CASH_SENSORS, CASH_SOURCE,
    PRESETS, REWARD_SENSORS, SOURCE, SOURCE_DATE, cash_values, number, reward_values,
)

POINT_DESCRIPTIONS = {
    "points": "Aktueller Gesamtpunktestand laut MakerWorld. Bereits ausgegebene Punkte sind darin berücksichtigt.",
    "points_regular": "Aktuell vorhandene reguläre Punkte auf deinem MakerWorld-Konto.",
    "points_exclusive": "Aktuell vorhandene exklusive Punkte. Deren USD-Gegenwert und die Auszahlungsgrenzen stehen in der Gruppe USD-Auszahlung.",
    "points_earned": "Summe der bisher gutgeschriebenen regulären Punkte laut Transaktionssummen. Einlösungen vermindern diesen Gesamtverdienst nicht.",
    "points_earned_exclusive": "Summe der bisher gutgeschriebenen exklusiven Punkte laut Transaktionssummen.",
    "points_spent": "Summe der bisher ausgegebenen regulären Punkte laut MakerWorld.",
    "points_spent_exclusive": "Summe der bisher ausgegebenen exklusiven Punkte laut MakerWorld.",
    "points_income_total": "Bisher gutgeschriebene reguläre und exklusive Punkte zusammen. Die Sensoren für 7, 14 und 30 Tage betrachten dagegen ein begrenztes Buchungszeitfenster.",
    "points_expense_total": "Bisher ausgegebene reguläre und exklusive Punkte zusammen.",
}
GIFT_DESCRIPTIONS = {
    "reward_balance_value": "Anteilig umgerechneter Wert des aktuellen Punktestands nach gewählter Gutschein-Punktebasis und Shopkurs. Beispiel: 800 Punkte entsprechen bei 40 EUR für 524 Punkte rechnerisch 61,07 EUR.",
    "reward_earned_value": "Bisher insgesamt verdiente Punkte der gewählten Punktebasis, umgerechnet zum aktuellen Gutschein-Kurs. Dieser Wert enthält auch inzwischen ausgegebene Punkte.",
    "reward_cards": "Anzahl vollständiger Guthaben-Gutscheine, die der aktuelle Punktestand rechnerisch finanziert. Beispiel: 800 Punkte reichen bei 524 Punkten je Gutschein für einen Gutschein.",
    "reward_credit": "Guthaben der rechnerisch finanzierbaren ganzen Gutscheine. Beispiel: Ein Gutschein zu 40 EUR ergibt 40 EUR Guthaben. Restpunkte zählen erst beim nächsten vollständigen Gutschein.",
    "reward_missing": "Zusätzlich benötigte Punkte bis zu einem weiteren vollständigen Gutschein. Bei einer genau erreichten Schwelle beginnt die Zählung für den folgenden Gutschein.",
    "reward_progress": "Fortschritt der Restpunkte zum nächsten vollständigen Gutschein in Prozent. Nach Erreichen eines Gutscheins beginnt die Anzeige wieder bei null.",
}
CASH_DESCRIPTIONS = {
    "cash_balance_value": "Aktuell vorhandene exklusive Punkte × 0,066 USD. Dieser Gegenwert kann auch unter der Mindestgrenze von 100 USD liegen.",
    "cash_earned_value": "Bisher insgesamt verdiente exklusive Punkte × 0,066 USD. Einschließlich inzwischen ausgegebener Punkte. Der Wert beschreibt den Gesamtverdienst als Gegenwert.",
    "cash_claimable": "Rechnerisch beantragbarer Betrag aus den vorhandenen exklusiven Punkten, begrenzt durch den Gesamtpunktestand. Unter 100 USD beträgt er null, pro Antrag höchstens 1.000 USD. MakerWorld prüft den Antrag.",
    "cash_missing_usd": "Fehlender USD-Gegenwert bis zum Mindestantrag von 100 USD, unter Berücksichtigung des Gesamtpunktestands.",
    "cash_missing_points": "Zusätzlich benötigte Punkte bis zum Mindestantrag von 100 USD. Der Wert wird auf drei Nachkommastellen aufgerundet.",
    "cash_progress": "Fortschritt zur Mindestgrenze von 100 USD, unter Berücksichtigung des Gesamtpunktestands. Die Anzeige endet bei 100 Prozent.",
}


# Snapshot values can decrease when models or activity are removed.
SENSORS = (
    ("design_downloads", "Downloads Modelle", "mdi:download"),
    ("instance_downloads", "Downloads Druckprofile", "mdi:download"),
    ("total_downloads", "Downloads kombiniert", "mdi:download-multiple"),
    ("design_prints", "Drucke Modelle", "mdi:printer-3d"),
    ("instance_prints", "Drucke Druckprofile", "mdi:printer-3d"),
    ("total_prints", "Drucke kombiniert", "mdi:printer-3d"),
    ("designs", "Veröffentlichte Modelle", "mdi:cube-outline"),
    ("likes", "Likes", "mdi:thumb-up"),
    ("collections", "Sammlungen", "mdi:bookmark-multiple"),
    ("followers", "Follower", "mdi:account-group"),
    ("following", "Gefolgte Konten", "mdi:account-multiple-plus"),
    ("level", "Level", "mdi:trophy-outline"),
    ("points", "Punkte – Kontostand gesamt", "mdi:cash-multiple"),
    ("points_regular", "Reguläre Punkte – Kontostand", "mdi:cash"),
    ("points_exclusive", "Exklusive Punkte – Kontostand", "mdi:cash"),
    ("points_earned", "Reguläre Punkte – Insgesamt verdient", "mdi:cash-plus"),
    ("points_spent", "Reguläre Punkte – Insgesamt ausgegeben", "mdi:cash-minus"),
    ("points_earned_exclusive", "Exklusive Punkte – Insgesamt verdient", "mdi:cash-plus"),
    ("points_spent_exclusive", "Exklusive Punkte – Insgesamt ausgegeben", "mdi:cash-minus"),
    ("points_income_total", "Punkte insgesamt verdient", "mdi:cash-plus"),
    ("points_expense_total", "Punkte insgesamt ausgegeben", "mdi:cash-minus"),
    ("boosts_received", "Boosts erhalten", "mdi:rocket-launch-outline"),
    ("boost_tokens", "Boost-Tokens verfügbar", "mdi:rocket-launch"),
    ("boosts_used", "Boost-Tokens verwendet", "mdi:rocket"),
    ("boosts_expired", "Boost-Tokens verfallen", "mdi:rocket-outline"),
)


async def async_setup_entry(hass, entry, async_add_entities):
    registry = er.async_get(hass)
    prefix = f"{entry.runtime_data.account_id}_"
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if entity.platform != DOMAIN or not entity.unique_id.startswith(prefix):
            continue
        key = entity.unique_id[len(prefix):]
        if sensor_group(key) and not show_sensor(key, entry.options):
            registry.async_remove(entity.entity_id)
    async_add_entities(
        MakerWorldSensor(
            entry.runtime_data,
            SensorEntityDescription(
                key=key, name=name, icon=icon,
                state_class=SensorStateClass.MEASUREMENT,
            ),
        )
        for key, name, icon in SENSORS
    )
    async_add_entities(
        MakerWorldRewardSensor(entry.runtime_data, key, name, icon, kind)
        for key, name, icon, kind in (*REWARD_SENSORS, *CASH_SENSORS)
        if show_sensor(key, entry.options)
    )
    async_add_entities(
        MakerWorldIncomeSensor(entry.runtime_data, days, kind)
        for days in (7, 14, 30)
        for kind in ("points", "money", "cash")
        if show_sensor(f"income_{kind}_{days}d", entry.options)
    )


class MakerWorldSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.account_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.account_id)},
            name=f"MakerWorld {coordinator.data.name or coordinator.account_id}",
            manufacturer="Bambu Lab",
            model="MakerWorld-Konto",
        )

    @property
    def available(self):
        return super().available and self.native_value is not None

    @property
    def native_value(self):
        return getattr(self.coordinator.data, self.entity_description.key, None)

    @property
    def extra_state_attributes(self):
        key = self.entity_description.key
        description = POINT_DESCRIPTIONS.get(key)
        return {"beschreibung": description} if description else {}


class MakerWorldRewardSensor(MakerWorldSensor):
    """Local estimates with explicit terms and no mixed-currency statistics."""

    def __init__(self, coordinator, key, name, icon, kind):
        super().__init__(coordinator, SensorEntityDescription(key=key, name=name, icon=icon))
        self._kind = kind

    @property
    def native_value(self):
        if self.entity_description.key.startswith("cash_"):
            return cash_values(self.coordinator.data).get(self.entity_description.key)
        return reward_values(self.coordinator.data, self.coordinator.reward_options).get(self.entity_description.key)

    @property
    def native_unit_of_measurement(self):
        if self._kind == "cash":
            return "USD"
        if self._kind == "money":
            return self.coordinator.reward_options.get("currency")
        return {"percent": "%", "points": "Punkte"}.get(self._kind)

    @property
    def extra_state_attributes(self):
        if self.entity_description.key.startswith("cash_"):
            return {
                "beschreibung": CASH_DESCRIPTIONS[self.entity_description.key],
                "usd_per_exclusive_point": float(CASH_RATE),
                "minimum_usd": float(CASH_MIN),
                "maximum_usd_per_request": float(CASH_MAX),
                "limited_by_total_balance": True,
                "estimate": True,
                "subject_to_review": True,
                "rate_source": CASH_SOURCE,
                "terms_confirmed_by_user": "2026-11-10",
            }
        options = self.coordinator.reward_options
        preset = options.get("shop_region") in PRESETS
        modified = False
        if preset:
            currency, value, points = PRESETS[options["shop_region"]]
            modified = (
                options.get("currency") != currency
                or number(options.get("card_value")) != number(value)
                or number(options.get("card_points")) != number(points)
            )
        rate_status = "user_defined"
        if preset and not modified:
            rate_status = "user_confirmed" if options.get("shop_region") == "eu" else "experimental"
        return {
            "beschreibung": GIFT_DESCRIPTIONS.get(self.entity_description.key),
            "rate_modified": modified,
            "shop_region": options.get("shop_region", "unset"),
            "points_basis": options.get("points_basis", "regular"),
            "card_value": options.get("card_value"),
            "card_points": options.get("card_points"),
            "experimental": preset and options.get("shop_region") != "eu",
            "rate_status": rate_status,
            "confirmation_date": "2026-11-10" if options.get("shop_region") == "eu" and not modified else None,
            "rate_source": SOURCE if preset and not modified else "user_settings",
            "rate_source_date": SOURCE_DATE if preset else None,
            "estimate": True,
        }


class MakerWorldIncomeSensor(MakerWorldRewardSensor):
    """Rolling income by booking timestamp, with cash and gift-card estimates."""

    def __init__(self, coordinator, days, kind):
        basis_name = "regulär"
        if coordinator.reward_options.get("sensor_view") == "cash":
            basis_name = "exklusiv"
        elif coordinator.reward_options.get("points_basis") == "combined":
            basis_name = "gesamt"
        names = {
            "points": f"Punkte {basis_name} – Einnahmen",
            "money": "Gutscheine – Einnahmen-Gegenwert",
            "cash": "USD-Auszahlung – Einnahmen-Gegenwert",
        }
        super().__init__(coordinator, f"income_{kind}_{days}d", f"{names[kind]} {days} Tage", "mdi:chart-line", kind)
        self._days = days

    @property
    def native_value(self):
        coordinator = self.coordinator
        if coordinator.income_events is None or coordinator.history_error or time.time() - coordinator.history_synced_at > HISTORY_INTERVAL * 2:
            return None
        basis = coordinator.reward_options.get("points_basis", "regular")
        if self._kind == "cash" or coordinator.reward_options.get("sensor_view") == "cash":
            basis = "exclusive"
        points = income_in_window(coordinator.income_events, basis, self._days, time.time())
        if points is None:
            return None
        if self._kind == "cash":
            return float((points * CASH_RATE).quantize(Decimal("0.01"), rounding=ROUND_DOWN))
        if self._kind == "money":
            profile = MakerWorldProfile(points_earned=points, points_income_total=points)
            return reward_values(profile, coordinator.reward_options).get("reward_earned_value")
        return float(points)

    @property
    def extra_state_attributes(self):
        attributes = dict(super().extra_state_attributes)
        if self._kind == "cash":
            attributes.update(currency="USD", usd_per_exclusive_point=float(CASH_RATE), points_basis="exclusive")
        attributes.update(
            beschreibung="Positive Punktegutschriften nach Buchungszeitpunkt in den letzten "
                f"{self._days} × 24 Stunden. Ausgaben werden nicht abgezogen. "
                "Geldwerte sind zum aktuellen Kurs umgerechnete Gegenwerte. Aktualisierung alle sechs Stunden.",
            window_days=self._days,
            time_basis="transaction_booking_timestamp",
            history_synced_at=self.coordinator.history_synced_at or None,
            history_error=self.coordinator.history_error,
            history_refresh_minutes=HISTORY_INTERVAL // 60,
            history_cache_persisted=self.coordinator.history_persisted,
            availability_checked=False,
        )
        if self.coordinator.reward_options.get("sensor_view") == "cash":
            attributes["points_basis"] = "exclusive"
        return attributes
