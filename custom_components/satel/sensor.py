"""Satel sensors."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo

from . import SatelHub
from .const import DOMAIN
from .entity import SatelEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
 codex/add-translations-for-custom-components
    hub: SatelHub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SatelStatusSensor(hub)], True)


class SatelStatusSensor(SensorEntity):
    """Representation of Satel status sensor."""

    _attr_translation_key = "status"

    def __init__(self, hub: SatelHub) -> None:
        self._hub = hub
        self._attr_native_unit_of_measurement = None
        self._attr_unique_id = "satel_status"
=======
    data = hass.data[DOMAIN][entry.entry_id]
    hub: SatelHub = data["hub"]
    devices = data["devices"]
    entities = [
        SatelZoneSensor(hub, zone["id"], zone["name"])
        for zone in devices.get("zones", [])
    ]
    async_add_entities(entities, True)


class SatelZoneSensor(SatelEntity, SensorEntity):
    """Representation of Satel zone status sensor."""

    def __init__(self, hub: SatelHub, zone_id: str, name: str) -> None:
        super().__init__(hub)
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
 main

    async def async_update(self) -> None:
        try:
            self._attr_native_value = await self._hub.send_command(
                f"ZONE {self._zone_id} STATUS"
            )
            self._attr_available = True
        except ConnectionError as err:
            _LOGGER.warning(
                "Could not update zone %s status sensor: %s", self._zone_id, err
            )
            self._attr_available = False
