"""Satel sensor platform."""

from __future__ import annotations

import logging
try:
    from homeassistant.components.sensor import SensorEntity
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
except ModuleNotFoundError:  # pragma: no cover - simple stubs
    class SensorEntity:  # type: ignore
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
    """Set up Satel sensors based on a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    hub: SatelHub = data["hub"]
    devices = data.get("devices", {})

    entities: list[SensorEntity] = []
    zones = devices.get("zones") or []
    if zones:
        entities.extend(
            SatelZoneSensor(hub, zone["id"], zone.get("name", zone["id"]))
            for zone in zones
        )
    else:
        entities.append(SatelStatusSensor(hub))

    async_add_entities(entities, True)


class SatelZoneSensor(SatelEntity, SensorEntity):
    """Sensor representing a Satel zone status."""

    def __init__(self, hub: SatelHub, zone_id: str, name: str) -> None:
        super().__init__(hub)
        self._zone_id = zone_id
        self._attr_name = f"{name} status"
        self._attr_unique_id = f"satel_zone_status_{zone_id}"
        self._attr_native_value = None

    async def async_update(self) -> None:
        try:
            self._attr_native_value = await self._hub.send_command(
                f"ZONE {self._zone_id} STATUS"
            )
            self._attr_available = True
        except ConnectionError as err:
            _LOGGER.warning("Failed to update zone %s status: %s", self._zone_id, err)
            self._attr_native_value = None
            self._attr_available = False


class SatelStatusSensor(SatelEntity, SensorEntity):
    """Sensor returning raw status string."""

    _attr_unique_id = "satel_status"
    _attr_name = "Satel Status"

    async def async_update(self) -> None:
        try:
            status = await self._hub.get_status()
            self._attr_native_value = status.get("raw")
            self._attr_available = True
        except ConnectionError as err:
            _LOGGER.warning("Failed to update status: %s", err)
            self._attr_native_value = None
            self._attr_available = False
