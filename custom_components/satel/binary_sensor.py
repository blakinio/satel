"""Satel binary sensor platform."""

from __future__ import annotations

import logging

try:
    from homeassistant.components.binary_sensor import BinarySensorEntity
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
except ModuleNotFoundError:  # pragma: no cover - simple stubs
    class BinarySensorEntity:  # type: ignore
        pass

    class ConfigEntry:  # type: ignore
        pass

    class HomeAssistant:  # type: ignore
        pass

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

    entities: list[BinarySensorEntity] = []
    zones = devices.get("zones") or []
    if zones:
        entities.extend(
            SatelZoneBinarySensor(hub, zone["id"], zone.get("name", zone["id"]))
            for zone in zones
        )
    else:
        entities.append(SatelAlarmBinarySensor(hub))

    async_add_entities(entities, True)


class SatelZoneBinarySensor(SatelEntity, BinarySensorEntity):
    """Binary sensor for a Satel zone."""

    _attr_translation_key = "zone"

    def __init__(self, hub: SatelHub, zone_id: str, name: str) -> None:
        super().__init__(hub)
        self._zone_id = zone_id
        self._attr_name = name
        self._attr_unique_id = f"satel_zone_{zone_id}"
        self._attr_is_on = None

    async def async_update(self) -> None:
        """Fetch zone state from the hub."""
        try:
            status = await self._hub.send_command(f"ZONE {self._zone_id}")
            self._attr_is_on = status.upper() == "ON"
            self._attr_available = True
        except ConnectionError as err:
            _LOGGER.warning("Failed to update zone %s: %s", self._zone_id, err)
            self._attr_is_on = None
            self._attr_available = False


class SatelAlarmBinarySensor(SatelEntity, BinarySensorEntity):
    """Binary sensor representing overall alarm state."""

    _attr_unique_id = "satel_alarm"
    _attr_name = "Satel Alarm"

    async def async_update(self) -> None:
        try:
            status = await self._hub.get_status()
            self._attr_is_on = status.get("raw") == "ALARM"
            self._attr_available = True
        except ConnectionError as err:
            _LOGGER.warning("Failed to update alarm status: %s", err)
            self._attr_is_on = None
            self._attr_available = False

