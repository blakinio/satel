"""Satel sensor platform."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import SatelHub
from .const import DOMAIN
from .entity import SatelEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up Satel sensors based on a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    hub: SatelHub = data["hub"]
    devices = data.get("devices", {})
    coordinator = data["coordinator"]

    entities: list[SensorEntity] = []
    zones = devices.get("zones") or []
    if zones:
        entities.extend(
            SatelZoneSensor(hub, coordinator, zone["id"], zone.get("name", zone["id"]))
            for zone in zones
        )
    else:
        entities.append(SatelStatusSensor(hub, coordinator))

    async_add_entities(entities)


class SatelZoneSensor(SatelEntity, SensorEntity):
    """Sensor representing a Satel zone status."""

    _attr_translation_key = "zone_status"

    def __init__(
        self, hub: SatelHub, coordinator, zone_id: str, name: str
    ) -> None:
        super().__init__(hub, coordinator)
        self._zone_id = zone_id
        self._attr_name = f"{name} status"
        self._attr_unique_id = f"satel_zone_status_{zone_id}"

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.get("zones", {}).get(self._zone_id)


class SatelStatusSensor(SatelEntity, SensorEntity):
    """Sensor returning raw status string."""

    _attr_unique_id = "satel_status"
    _attr_name = "Satel Status"

    def __init__(self, hub: SatelHub, coordinator) -> None:
        super().__init__(hub, coordinator)

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.get("alarm")

