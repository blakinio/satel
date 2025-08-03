"""Satel switch platform."""

from __future__ import annotations

import logging
try:
    from homeassistant.components.switch import SwitchEntity
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
except ModuleNotFoundError:  # pragma: no cover - simple stubs
    class SwitchEntity:  # type: ignore
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
    """Set up Satel switches based on a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    hub: SatelHub = data["hub"]
    devices = data.get("devices", {})

    entities: list[SwitchEntity] = [
        SatelOutputSwitch(hub, output["id"], output.get("name", output["id"]))
        for output in devices.get("outputs", [])
    ]

    async_add_entities(entities, True)


class SatelOutputSwitch(SatelEntity, SwitchEntity):
    """Switch to control Satel outputs."""

    def __init__(self, hub: SatelHub, output_id: str, name: str) -> None:
        super().__init__(hub)
        self._output_id = output_id
        self._attr_name = name
        self._attr_unique_id = f"satel_output_{output_id}"
        self._attr_is_on = False

    async def async_turn_on(self, **kwargs) -> None:
        try:
            await self._hub.send_command(f"OUTPUT {self._output_id} ON")
        except ConnectionError as err:
            _LOGGER.warning("Failed to turn on output %s: %s", self._output_id, err)
            return
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        try:
            await self._hub.send_command(f"OUTPUT {self._output_id} OFF")
        except ConnectionError as err:
            _LOGGER.warning("Failed to turn off output %s: %s", self._output_id, err)
            return
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_update(self) -> None:
        try:
            state = await self._hub.send_command(f"OUTPUT {self._output_id} STATE")
            self._attr_is_on = state.upper() == "ON"
            self._attr_available = True
        except ConnectionError as err:
            _LOGGER.warning("Failed to update output %s: %s", self._output_id, err)
            self._attr_is_on = None
            self._attr_available = False
