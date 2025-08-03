"""Satel binary sensors."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import SatelHub
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    hub: SatelHub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SatelAlarmBinarySensor(hub)], True)


class SatelAlarmBinarySensor(BinarySensorEntity):
    """Binary sensor indicating alarm state."""

    _attr_name = "Satel Alarm"

    def __init__(self, hub: SatelHub) -> None:
        self._hub = hub
        self._attr_unique_id = "satel_alarm"

    async def async_update(self) -> None:
        data = await self._hub.get_status()
        self._attr_is_on = data.get("raw") == "ALARM"
