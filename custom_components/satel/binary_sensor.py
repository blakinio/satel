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
    """Set up Satel zone binary sensors based on config entry."""
    hub: SatelHub = hass.data[DOMAIN][entry.entry_id]
    status = await hub.get_status()
    entities = [SatelZoneBinarySensor(hub, zone) for zone in status["zones"]]
    async_add_entities(entities, True)


class SatelZoneBinarySensor(BinarySensorEntity):
    """Binary sensor representing a Satel zone."""

    def __init__(self, hub: SatelHub, zone_id: str) -> None:
        self._hub = hub
        self._zone_id = zone_id
        self._attr_unique_id = f"satel_zone_{zone_id}"
        self._attr_name = f"Satel Zone {zone_id}"

    async def async_update(self) -> None:
        data = await self._hub.get_status()
        self._attr_is_on = data["zones"].get(self._zone_id, False)

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, "satel")},
            "name": "Satel Alarm",
            "manufacturer": "Satel",
        }

