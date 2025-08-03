"""Satel switches."""

from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo

from . import SatelHub
from .const import DOMAIN
from .entity import SatelEntity

_LOGGER = logging.getLogger(__name__)


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
codex/implement-dynamic-entity-creation-and-updates
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
=======
    data = hass.data[DOMAIN][entry.entry_id]
    hub: SatelHub = data["hub"]
    devices = data["devices"]
    entities = [
        SatelOutputSwitch(hub, output["id"], output["name"])
        for output in devices.get("outputs", [])
    ]
    async_add_entities(entities, True)


class SatelOutputSwitch(SatelEntity, SwitchEntity):
    """Switch to control Satel output."""

 codex/add-translations-for-custom-components
    _attr_translation_key = "output"

    def __init__(self, hub: SatelHub) -> None:
        self._hub = hub
=======
    def __init__(self, hub: SatelHub, output_id: str, name: str) -> None:
        super().__init__(hub)
        self._output_id = output_id
        self._attr_name = name
 main
        self._attr_is_on = False
        self._attr_unique_id = f"satel_output_{output_id}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._hub.host)},
            manufacturer="Satel",
            name="Satel Alarm",
        )

    async def async_turn_on(self, **kwargs) -> None:
 codex/validate-response-after-sending-output-on/off
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
=======
        try:
            await self._hub.send_command(f"OUTPUT {self._output_id} ON")
 codex/wrap-send_command-in-try/except-for-connection-errors
        except ConnectionError as err:
            _LOGGER.warning("Failed to turn on output %s: %s", self._output_id, err)
            return
 main
        self._attr_is_on = True
        self.async_write_ha_state()
 zquiz2-codex/update-async_turn_on-and-async_turn_off-methods
=======
=======
            self._attr_is_on = True
            self._attr_available = True
            self.async_write_ha_state()
        except ConnectionError as err:
            _LOGGER.warning(
                "Failed to turn on output %s: %s", self._output_id, err
            )
            self._attr_available = False
 main
 main

    async def async_turn_off(self, **kwargs) -> None:
 codex/implement-dynamic-entity-creation-and-updates
        await self._hub.send_command(f"OUTPUT {self._output_id} OFF")
=======
        try:
            await self._hub.send_command(f"OUTPUT {self._output_id} OFF")
 codex/wrap-send_command-in-try/except-for-connection-errors
        except ConnectionError as err:
            _LOGGER.warning("Failed to turn off output %s: %s", self._output_id, err)
            return
 main
        self._attr_is_on = False
        self.async_write_ha_state()
 zquiz2-codex/update-async_turn_on-and-async_turn_off-methods
=======
=======
            self._attr_is_on = False
            self._attr_available = True
            self.async_write_ha_state()
        except ConnectionError as err:
            _LOGGER.warning(
                "Failed to turn off output %s: %s", self._output_id, err
            )
            self._attr_available = False
 main
 codex/validate-response-after-sending-output-on/off
=======
 main
 main

    async def async_update(self) -> None:
codex/implement-dynamic-entity-creation-and-updates
        data = await self._hub.get_status()
        self._attr_is_on = data["outputs"].get(self._output_id, False)

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, "satel")},
            "name": "Satel Alarm",
            "manufacturer": "Satel",
        }

=======
        try:
            state = await self._hub.send_command(f"OUTPUT {self._output_id} STATE")
 codex/wrap-send_command-in-try/except-for-connection-errors
        except ConnectionError as err:
            _LOGGER.warning("Failed to update output %s: %s", self._output_id, err)
            self._attr_is_on = None
            return
        self._attr_is_on = state.upper() == "ON"
=======
            self._attr_is_on = state.upper() == "ON"
            self._attr_available = True
        except ConnectionError as err:
            _LOGGER.warning(
                "Failed to update state for output %s: %s", self._output_id, err
            )
            self._attr_available = False
 main
 main
