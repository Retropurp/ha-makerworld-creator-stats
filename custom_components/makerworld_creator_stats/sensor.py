"""All account statistics exposed as individual sensors."""

from decimal import Decimal, ROUND_DOWN
import time

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .profile import MakerWorldProfile
from .transactions import HISTORY_INTERVAL, income_in_window
from .rewards import (
    CASH_MAX, CASH_MIN, CASH_RATE, CASH_SENSORS, CASH_SOURCE,
    PRESETS, REWARD_SENSORS, SOURCE, SOURCE_DATE, cash_values, number, reward_values,
)


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
    ("points", "Punkte gesamt", "mdi:cash-multiple"),
    ("points_regular", "Reguläre Punkte", "mdi:cash"),
    ("points_exclusive", "Exklusive Punkte", "mdi:cash"),
    ("points_earned", "Reguläre Punkte verdient", "mdi:cash-plus"),
    ("points_spent", "Reguläre Punkte ausgegeben", "mdi:cash-minus"),
    ("points_earned_exclusive", "Exklusive Punkte verdient", "mdi:cash-plus"),
    ("points_spent_exclusive", "Exklusive Punkte ausgegeben", "mdi:cash-minus"),
    ("points_income_total", "Punkte insgesamt verdient", "mdi:cash-plus"),
    ("points_expense_total", "Punkte insgesamt ausgegeben", "mdi:cash-minus"),
    ("boosts_received", "Boosts erhalten", "mdi:rocket-launch-outline"),
    ("boost_tokens", "Boost-Tokens verfügbar", "mdi:rocket-launch"),
    ("boosts_used", "Boost-Tokens verwendet", "mdi:rocket"),
    ("boosts_expired", "Boost-Tokens verfallen", "mdi:rocket-outline"),
)


async def async_setup_entry(hass, entry, async_add_entities):
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
    )
    async_add_entities(
        MakerWorldIncomeSensor(entry.runtime_data, days, kind)
        for days in (7, 14, 30)
        for kind in ("points", "money", "cash")
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
        names = {
            "points": "Punkte-Einnahmen",
            "money": "Einnahmen Gutschein-Gegenwert",
            "cash": "Exklusive Einnahmen USD-Gegenwert",
        }
        super().__init__(coordinator, f"income_{kind}_{days}d", f"{names[kind]} {days} Tage", "mdi:chart-line", kind)
        self._days = days

    @property
    def native_value(self):
        coordinator = self.coordinator
        if coordinator.income_events is None or coordinator.history_error or time.time() - coordinator.history_synced_at > HISTORY_INTERVAL * 2:
            return None
        basis = coordinator.reward_options.get("points_basis", "regular")
        if self._kind == "cash":
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
            window_days=self._days,
            time_basis="transaction_booking_timestamp",
            history_synced_at=self.coordinator.history_synced_at or None,
            history_error=self.coordinator.history_error,
            history_refresh_minutes=HISTORY_INTERVAL // 60,
            history_cache_persisted=self.coordinator.history_persisted,
            availability_checked=False,
        )
        return attributes
