"""Satel sensors."""

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
    """Set up Satel zone sensors from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    hub: SatelHub = data["hub"]
    devices = data["devices"]
    entities = [
        SatelZoneSensor(hub, zone["id"], zone["name"])
        for zone in devices.get("zones", [])
    ]
    async_add_entities(entities)


class SatelZoneSensor(SatelEntity, SensorEntity):
    """Representation of Satel zone status sensor."""

    _attr_translation_key = "zone_status"

    def __init__(self, hub: SatelHub, zone_id: str, name: str) -> None:
        super().__init__(hub)
        self._zone_id = zone_id
        self._attr_name = f"{name} status"
        self._attr_unique_id = f"satel_zone_status_{zone_id}"
        self._attr_native_value: str | None = None

    async def async_update(self) -> None:
        """Update the sensor state."""
        try:
            value = await self._hub.send_command(f"ZONE {self._zone_id} STATUS")
        except ConnectionError as err:
            _LOGGER.warning("Failed to update zone %s: %s", self._zone_id, err)
            self._attr_native_value = None
            return
        self._attr_native_value = value.strip()

