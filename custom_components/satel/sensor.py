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
    """Set up Satel zone sensors based on config entry."""
    hub: SatelHub = hass.data[DOMAIN][entry.entry_id]
    status = await hub.get_status()
    entities = [SatelZoneSensor(hub, zone) for zone in status["zones"]]
    async_add_entities(entities, True)


class SatelZoneSensor(SensorEntity):
    """Representation of a Satel zone sensor."""

    def __init__(self, hub: SatelHub, zone_id: str) -> None:
        self._hub = hub
        self._zone_id = zone_id
        self._attr_unique_id = f"satel_zone_sensor_{zone_id}"
        self._attr_name = f"Satel Zone {zone_id}"

    async def async_update(self) -> None:
        data = await self._hub.get_status()
        self._attr_native_value = "on" if data["zones"].get(self._zone_id) else "off"

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, "satel")},
            "name": "Satel Alarm",
            "manufacturer": "Satel",
        }

