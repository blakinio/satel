"""Satel binary sensor platform."""

from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import SatelHub
from .const import DOMAIN
from .entity import SatelEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up Satel binary sensors based on a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    hub: SatelHub = data["hub"]
    devices = data.get("devices", {})
    coordinator = data["coordinator"]

    entities: list[BinarySensorEntity] = []
    zones = devices.get("zones") or []
    if zones:
        entities.extend(
            SatelZoneBinarySensor(hub, coordinator, zone["id"], zone.get("name", zone["id"]))
            for zone in zones
        )
    else:
        entities.append(SatelAlarmBinarySensor(hub, coordinator))

    async_add_entities(entities)


class SatelZoneBinarySensor(SatelEntity, BinarySensorEntity):
    """Binary sensor for a Satel zone."""

    _attr_translation_key = "zone"
    _attr_device_class = BinarySensorDeviceClass.MOTION

    def __init__(
        self, hub: SatelHub, coordinator, zone_id: str, name: str
    ) -> None:
        super().__init__(hub, coordinator)
        self._zone_id = zone_id
        self._attr_name = name
        self._attr_unique_id = f"satel_zone_{zone_id}"

    @property
    def is_on(self) -> bool | None:
        status = self.coordinator.data.get("zones", {}).get(self._zone_id)
        if status is None:
            return None
        return status.upper() == "ON"

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        data = self.coordinator.data
        return {
            "troubles": data.get("troubles", {}).get(self._zone_id),
            "tamper": data.get("tamper", {}).get(self._zone_id),
            "bypass": data.get("bypass", {}).get(self._zone_id),
            "alarm_memory": data.get("alarm_memory", {}).get(self._zone_id),
        }


class SatelAlarmBinarySensor(SatelEntity, BinarySensorEntity):
    """Binary sensor representing overall alarm state."""

    _attr_unique_id = "satel_alarm"
    _attr_name = "Satel Alarm"

    def __init__(self, hub: SatelHub, coordinator) -> None:
        super().__init__(hub, coordinator)

    @property
    def is_on(self) -> bool:
        alarm = self.coordinator.data.get("alarm")
        if isinstance(alarm, dict):
            return any(state.upper() == "TRIGGERED" for state in alarm.values())
        return str(alarm).upper() == "ALARM"

