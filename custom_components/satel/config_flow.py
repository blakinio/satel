"""Config flow for Satel integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from . import SatelHub
from .const import DOMAIN, DEFAULT_PORT, DEFAULT_HOST


class SatelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Satel."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._port = user_input[CONF_PORT]
            hub = SatelHub(self._host, self._port)
            try:
                await hub.connect()
                self._devices = await hub.discover_devices()
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "cannot_connect"
            else:
                return await self.async_step_select()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            }
        )
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def async_step_select(self, user_input=None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title=f"Satel {self._host}",
                data={
                    CONF_HOST: self._host,
                    CONF_PORT: self._port,
                    "zones": user_input.get("zones", []),
                    "outputs": user_input.get("outputs", []),
                },
            )

        zone_options = {z["id"]: z["name"] for z in self._devices.get("zones", [])}
        output_options = {o["id"]: o["name"] for o in self._devices.get("outputs", [])}
        data_schema = vol.Schema(
            {
                vol.Optional("zones", default=list(zone_options)): cv.multi_select(zone_options),
                vol.Optional("outputs", default=list(output_options)): cv.multi_select(output_options),
            }
        )
        return self.async_show_form(step_id="select", data_schema=data_schema)
