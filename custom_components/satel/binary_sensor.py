"""Satel binary sensors."""

from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
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
codex/implement-dynamic-entity-creation-and-updates
    """Set up Satel zone binary sensors based on config entry."""
=======
 codex/add-translations-for-custom-components
 main
    hub: SatelHub = hass.data[DOMAIN][entry.entry_id]
    status = await hub.get_status()
    entities = [SatelZoneBinarySensor(hub, zone) for zone in status["zones"]]
    async_add_entities(entities, True)


class SatelZoneBinarySensor(BinarySensorEntity):
    """Binary sensor representing a Satel zone."""

 codex/implement-dynamic-entity-creation-and-updates
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

=======
    _attr_translation_key = "alarm"

    def __init__(self, hub: SatelHub) -> None:
        self._hub = hub
        self._attr_unique_id = "satel_alarm"
=======
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
            status = await self._hub.send_command(f"ZONE {self._zone_id}")
 codex/wrap-send_command-in-try/except-for-connection-errors
        except ConnectionError as err:
            _LOGGER.warning("Failed to update zone %s: %s", self._zone_id, err)
            self._attr_is_on = None
            return
        self._attr_is_on = status.upper() == "ON"
=======
            self._attr_is_on = status.upper() == "ON"
            self._attr_available = True
        except ConnectionError as err:
            _LOGGER.warning(
                "Could not update zone %s status: %s", self._zone_id, err
            )
            self._attr_available = False
 main
 main
