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
    "points": "Current total point balance reported by MakerWorld, including points already spent.",
    "points_regular": "Regular points currently available in your MakerWorld account.",
    "points_exclusive": "Exclusive points currently available. Their estimated USD value and payout thresholds are listed under USD cash rewards.",
    "points_earned": "Regular points earned over the account lifetime. Redeeming points does not reduce this total.",
    "points_earned_exclusive": "Exclusive points earned over the account lifetime.",
    "points_spent": "Regular points spent over the account lifetime, as reported by MakerWorld.",
    "points_spent_exclusive": "Exclusive points spent over the account lifetime, as reported by MakerWorld.",
    "points_income_total": "Regular and exclusive points earned over the account lifetime. The rolling 7-, 14- and 30-day sensors use booking-date windows.",
    "points_expense_total": "Regular and exclusive points spent over the account lifetime.",
}
GIFT_DESCRIPTIONS = {
    "reward_balance_value": "Estimated current balance value based on the selected point basis and gift card terms. For example, 800 points at EUR 40 per 524 points correspond to approximately EUR 61.07.",
    "reward_earned_value": "Lifetime points earned using the selected point basis, converted at the currently configured gift card rate. This includes points already spent.",
    "reward_cards": "Whole gift cards affordable using the current eligible point balance, rounded down.",
    "reward_credit": "Total store credit represented by affordable whole gift cards. Any remaining points are excluded.",
    "reward_missing": "Additional points required to reach the next whole gift card. After a threshold, the following whole gift card becomes the target.",
    "reward_progress": "Progress toward the next gift card using remaining points, resetting to zero at each full-card threshold.",
}
CASH_DESCRIPTIONS = {
    "cash_balance_value": "Current exclusive points multiplied by USD 0.066. This estimated value may be below the USD 100 minimum payout.",
    "cash_earned_value": "Lifetime exclusive points earned multiplied by USD 0.066, including points already spent. This is an estimate, not an actual payment history.",
    "cash_claimable": "Estimated amount eligible for a payout request, limited by the current total point balance. A USD 100 minimum and USD 1,000 maximum per request apply. MakerWorld reviews actual requests.",
    "cash_missing_usd": "Estimated additional USD value required to reach the USD 100 minimum payout threshold, considering the available total point balance.",
    "cash_missing_points": "Estimated additional points needed for the USD 100 minimum payout threshold, rounded up to three decimal places.",
    "cash_progress": "Progress toward the USD 100 minimum payout threshold, considering available total points and capped at 100%.",
}


# Snapshot values can decrease when models or activity are removed.
SENSORS = (
    ("design_downloads", "Model downloads", "mdi:download"),
    ("instance_downloads", "Print profile downloads", "mdi:download"),
    ("total_downloads", "Combined downloads", "mdi:download-multiple"),
    ("design_prints", "Model prints", "mdi:printer-3d"),
    ("instance_prints", "Print profile prints", "mdi:printer-3d"),
    ("total_prints", "Combined prints", "mdi:printer-3d"),
    ("designs", "Published models", "mdi:cube-outline"),
    ("likes", "Likes", "mdi:thumb-up"),
    ("collections", "Collections", "mdi:bookmark-multiple"),
    ("followers", "Followers", "mdi:account-group"),
    ("following", "Following", "mdi:account-multiple-plus"),
    ("level", "Level", "mdi:trophy-outline"),
    ("points", "Total point balance", "mdi:cash-multiple"),
    ("points_regular", "Regular point balance", "mdi:cash"),
    ("points_exclusive", "Exclusive point balance", "mdi:cash"),
    ("points_earned", "Regular points earned (lifetime)", "mdi:cash-plus"),
    ("points_spent", "Regular points spent (lifetime)", "mdi:cash-minus"),
    ("points_earned_exclusive", "Exclusive points earned (lifetime)", "mdi:cash-plus"),
    ("points_spent_exclusive", "Exclusive points spent (lifetime)", "mdi:cash-minus"),
    ("points_income_total", "Total points earned (lifetime)", "mdi:cash-plus"),
    ("points_expense_total", "Total points spent (lifetime)", "mdi:cash-minus"),
    ("boosts_received", "Boosts received", "mdi:rocket-launch-outline"),
    ("boost_tokens", "Available boost tokens", "mdi:rocket-launch"),
    ("boosts_used", "Boost tokens used", "mdi:rocket"),
    ("boosts_expired", "Boost tokens expired", "mdi:rocket-outline"),
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
                key=key, translation_key=key, icon=icon,
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
            model="MakerWorld account",
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
        return {"description": description, "beschreibung": description} if description else {}


class MakerWorldRewardSensor(MakerWorldSensor):
    """Local estimates with explicit terms and no mixed-currency statistics."""

    def __init__(self, coordinator, key, name, icon, kind, translation_key=None):
        super().__init__(coordinator, SensorEntityDescription(
            key=key, translation_key=translation_key or key, icon=icon
        ))
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
        return {"percent": "%", "points": "points"}.get(self._kind)

    @property
    def extra_state_attributes(self):
        if self.entity_description.key.startswith("cash_"):
            return {
                "description": CASH_DESCRIPTIONS[self.entity_description.key],
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
            "description": GIFT_DESCRIPTIONS.get(self.entity_description.key),
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
        basis = "regular"
        if coordinator.reward_options.get("sensor_view") == "cash":
            basis = "exclusive"
        elif coordinator.reward_options.get("points_basis") == "combined":
            basis = "combined"
        translation_key = (
            f"income_points_{days}d_{basis}" if kind == "points"
            else f"income_{kind}_{days}d"
        )
        super().__init__(
            coordinator, f"income_{kind}_{days}d",
            f"{kind} earnings ({days} days)", "mdi:chart-line", kind,
            translation_key=translation_key,
        )
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
            description="Positive point credits booked within the last "
                f"{self._days} × 24 hours. Spending is not deducted. "
                "Monetary values use the currently configured estimate rate. "
                "Transaction history refreshes at most every six hours.",
            window_days=self._days,
            time_basis="transaction_booking_timestamp",
            history_synced_at=self.coordinator.history_synced_at or None,
            history_error=self.coordinator.history_error,
            history_refresh_minutes=HISTORY_INTERVAL // 60,
            history_cache_persisted=self.coordinator.history_persisted,
            availability_checked=False,
        )
        attributes["beschreibung"] = attributes["description"]
        if self.coordinator.reward_options.get("sensor_view") == "cash":
            attributes["points_basis"] = "exclusive"
        return attributes
