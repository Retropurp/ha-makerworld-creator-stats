"""All account statistics exposed as individual sensors."""

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


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
