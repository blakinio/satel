"""Satel sensors."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import SatelHub
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    hub: SatelHub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SatelStatusSensor(hub)], True)


class SatelStatusSensor(SensorEntity):
    """Representation of Satel status sensor."""

    _attr_name = "Satel Status"

    def __init__(self, hub: SatelHub) -> None:
        self._hub = hub
        self._attr_native_unit_of_measurement = None
        self._attr_unique_id = "satel_status"

    async def async_update(self) -> None:
        data = await self._hub.get_status()
        self._attr_native_value = data.get("raw")
