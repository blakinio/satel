"""Satel sensors."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo

from . import SatelHub
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    hub: SatelHub = data["hub"]
    devices = data["devices"]
    entities = [
        SatelZoneSensor(hub, zone["id"], zone["name"])
        for zone in devices.get("zones", [])
    ]
    async_add_entities(entities, True)


class SatelZoneSensor(SensorEntity):
    """Representation of Satel zone status sensor."""

    def __init__(self, hub: SatelHub, zone_id: str, name: str) -> None:
        self._hub = hub
        self._zone_id = zone_id
        self._attr_name = f"{name} status"
        self._attr_unique_id = f"satel_zone_status_{zone_id}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._hub.host)},
            manufacturer="Satel",
            name="Satel Alarm",
        )

    async def async_update(self) -> None:
        self._attr_native_value = await self._hub.send_command(
            f"ZONE {self._zone_id} STATUS"
        )
