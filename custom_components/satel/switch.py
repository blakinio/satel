"""Satel switch platform."""

from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import SatelHub
from .const import DOMAIN
from .entity import SatelEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up Satel switches based on a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    hub: SatelHub = data["hub"]
    devices = data.get("devices", {})
    coordinator = data["coordinator"]

    entities: list[SwitchEntity] = [
        SatelOutputSwitch(hub, coordinator, output["id"], output.get("name", output["id"]))
        for output in devices.get("outputs", [])
    ]

    async_add_entities(entities)


class SatelOutputSwitch(SatelEntity, SwitchEntity):
    """Switch to control Satel outputs."""

    _attr_translation_key = "output"

    def __init__(self, hub: SatelHub, coordinator, output_id: str, name: str) -> None:
        super().__init__(hub, coordinator)
        self._output_id = output_id
        self._attr_name = name
        self._attr_unique_id = f"satel_output_{output_id}"
        self._attr_is_on = False

    @property
    def is_on(self) -> bool:
        state = self.coordinator.data.get("outputs", {}).get(self._output_id)
        if state is None:
            return False
        return state.upper() == "ON"

    async def async_turn_on(self, **kwargs) -> None:  # noqa: D401
        """Turn the output on."""
        try:
            await self._hub.set_output(self._output_id, True)
        except ConnectionError as err:
            _LOGGER.warning("Failed to turn on output %s: %s", self._output_id, err)
            return
        self._attr_is_on = True
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:  # noqa: D401
        """Turn the output off."""
        try:
            await self._hub.set_output(self._output_id, False)
        except ConnectionError as err:
            _LOGGER.warning("Failed to turn off output %s: %s", self._output_id, err)
            return
        self._attr_is_on = False
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

