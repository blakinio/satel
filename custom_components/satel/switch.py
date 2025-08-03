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

 codex/clean-up-custom_components-code
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
=======
    class ConfigEntry:  # type: ignore
        pass

    class HomeAssistant:  # type: ignore
        pass
 main

from . import SatelHub
from .const import DOMAIN
from .entity import SatelEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
 codex/clean-up-custom_components-code
    """Set up Satel output switches from a config entry."""
=======
    """Set up Satel switches based on a config entry."""
 main
    data = hass.data[DOMAIN][entry.entry_id]
    hub: SatelHub = data["hub"]
    devices = data.get("devices", {})

    entities: list[SwitchEntity] = [
        SatelOutputSwitch(hub, output["id"], output.get("name", output["id"]))
        for output in devices.get("outputs", [])
    ]
 codex/clean-up-custom_components-code
    async_add_entities(entities)


class SatelOutputSwitch(SatelEntity, SwitchEntity):
    """Switch to control a Satel output."""

    _attr_translation_key = "output"

=======

    async_add_entities(entities, True)


class SatelOutputSwitch(SatelEntity, SwitchEntity):
    """Switch to control Satel outputs."""

 main
    def __init__(self, hub: SatelHub, output_id: str, name: str) -> None:
        super().__init__(hub)
        self._output_id = output_id
        self._attr_name = name
        self._attr_unique_id = f"satel_output_{output_id}"
 codex/clean-up-custom_components-code
        self._attr_is_on: bool | None = False

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the output on."""
=======
        self._attr_is_on = False

    async def async_turn_on(self, **kwargs) -> None:
 main
        try:
            await self._hub.send_command(f"OUTPUT {self._output_id} ON")
        except ConnectionError as err:
            _LOGGER.warning("Failed to turn on output %s: %s", self._output_id, err)
            return
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
 codex/clean-up-custom_components-code
        """Turn the output off."""
=======
 main
        try:
            await self._hub.send_command(f"OUTPUT {self._output_id} OFF")
        except ConnectionError as err:
            _LOGGER.warning("Failed to turn off output %s: %s", self._output_id, err)
            return
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_update(self) -> None:
 codex/clean-up-custom_components-code
        """Retrieve current state for the output."""
        try:
            state = await self._hub.send_command(f"OUTPUT {self._output_id} STATE")
        except ConnectionError as err:
            _LOGGER.warning("Failed to update output %s: %s", self._output_id, err)
            self._attr_is_on = None
            return
        self._attr_is_on = state.strip().upper() == "ON"

=======
        try:
            state = await self._hub.send_command(f"OUTPUT {self._output_id} STATE")
            self._attr_is_on = state.upper() == "ON"
            self._attr_available = True
        except ConnectionError as err:
            _LOGGER.warning("Failed to update output %s: %s", self._output_id, err)
            self._attr_is_on = None
            self._attr_available = False
 main
