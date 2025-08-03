"""Satel switches."""

from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import SatelHub
from .const import DOMAIN


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    hub: SatelHub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SatelOutputSwitch(hub)], True)


class SatelOutputSwitch(SwitchEntity):
    """Switch to control Satel output."""

    _attr_name = "Satel Output"

    def __init__(self, hub: SatelHub) -> None:
        self._hub = hub
        self._attr_is_on = False
        self._attr_unique_id = "satel_output"

    async def async_turn_on(self, **kwargs) -> None:
        response = await self._hub.send_command("OUTPUT ON")
        if response.strip().upper() == "OK":
            self._attr_is_on = True
        else:
            _LOGGER.error("Failed to turn on output: %s", response)

    async def async_turn_off(self, **kwargs) -> None:
        response = await self._hub.send_command("OUTPUT OFF")
        if response.strip().upper() == "OK":
            self._attr_is_on = False
        else:
            _LOGGER.error("Failed to turn off output: %s", response)

    async def async_update(self) -> None:
        # In real implementation, query hub for output state
        pass
