"""Satel switches."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import SatelHub
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up Satel output switches based on config entry."""
    hub: SatelHub = hass.data[DOMAIN][entry.entry_id]
    status = await hub.get_status()
    entities = [SatelOutputSwitch(hub, output) for output in status["outputs"]]
    async_add_entities(entities, True)


class SatelOutputSwitch(SwitchEntity):
    """Switch to control a Satel output."""

    def __init__(self, hub: SatelHub, output_id: str) -> None:
        self._hub = hub
        self._output_id = output_id
        self._attr_unique_id = f"satel_output_{output_id}"
        self._attr_name = f"Satel Output {output_id}"
        self._attr_is_on = False

    async def async_turn_on(self, **kwargs) -> None:
        await self._hub.send_command(f"OUTPUT {self._output_id} ON")
        self._attr_is_on = True

    async def async_turn_off(self, **kwargs) -> None:
        await self._hub.send_command(f"OUTPUT {self._output_id} OFF")
        self._attr_is_on = False

    async def async_update(self) -> None:
        data = await self._hub.get_status()
        self._attr_is_on = data["outputs"].get(self._output_id, False)

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, "satel")},
            "name": "Satel Alarm",
            "manufacturer": "Satel",
        }

