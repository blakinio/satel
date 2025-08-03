"""Satel binary sensors."""

from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import SatelHub
from .const import DOMAIN
from .entity import SatelEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    hub: SatelHub = data["hub"]
    devices = data["devices"]
    entities = [
        SatelZoneBinarySensor(hub, zone["id"], zone["name"])
        for zone in devices.get("zones", [])
    ]
    async_add_entities(entities, True)


class SatelZoneBinarySensor(SatelEntity, BinarySensorEntity):
    """Binary sensor for a Satel zone."""

    def __init__(self, hub: SatelHub, zone_id: str, name: str) -> None:
        super().__init__(hub)
        self._zone_id = zone_id
        self._attr_name = name
        self._attr_unique_id = f"satel_zone_{zone_id}"

    async def async_update(self) -> None:
        try:
            status = await self._hub.send_command(f"ZONE {self._zone_id}")
            self._attr_is_on = status.upper() == "ON"
            self._attr_available = True
        except ConnectionError as err:
            _LOGGER.warning(
                "Could not update zone %s status: %s", self._zone_id, err
            )
            self._attr_available = False
