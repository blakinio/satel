"""Config flow for the Satel integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT

 codex/clean-up-custom_components-code
from .const import DOMAIN, DEFAULT_HOST, DEFAULT_PORT
=======
from . import SatelHub
from .const import (
    DOMAIN,
    DEFAULT_HOST,
    DEFAULT_PORT,
    CONF_CODE,
    CONF_USER_CODE,
    CONF_ENCRYPTION_KEY,
    CONF_ENCODING,
    DEFAULT_ENCODING,
)
 main


class SatelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Satel."""

    VERSION = 1

 codex/clean-up-custom_components-code
    async def async_step_user(self, user_input=None):  # type: ignore[override]
        if user_input is not None:
            return self.async_create_entry(title="Satel", data=user_input)
=======
    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step of the flow."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._port = user_input[CONF_PORT]
            self._code = user_input[CONF_CODE]
            self._encoding = user_input.get(CONF_ENCODING, DEFAULT_ENCODING)

            hub = SatelHub(self._host, self._port, self._code, self._encoding)
            try:
                await hub.connect()
                self._devices = await hub.discover_devices()
            except (ConnectionError, OSError):
                errors["base"] = "cannot_connect"
            else:
                return await self.async_step_select()
 main

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
 codex/clean-up-custom_components-code
            }
        )
        return self.async_show_form(step_id="user", data_schema=data_schema)

=======
                vol.Required(CONF_CODE): str,
                vol.Optional(CONF_ENCODING, default=DEFAULT_ENCODING): str,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_select(self, user_input: dict | None = None) -> FlowResult:
        """Handle zone and output selection."""
        if user_input is not None:
            return self.async_create_entry(
                title=f"Satel {self._host}",
                data={
                    CONF_HOST: self._host,
                    CONF_PORT: self._port,
                    CONF_CODE: self._code,
                    CONF_ENCODING: self._encoding,
                    "zones": user_input.get("zones", []),
                    "outputs": user_input.get("outputs", []),
                },
            )

        zone_options = {z["id"]: z["name"] for z in self._devices.get("zones", [])}
        output_options = {o["id"]: o["name"] for o in self._devices.get("outputs", [])}

        data_schema = vol.Schema(
            {
                vol.Optional("zones", default=list(zone_options)): cv.multi_select(
                    zone_options
                ),
                vol.Optional("outputs", default=list(output_options)): cv.multi_select(
                    output_options
                ),
            }
        )
        return self.async_show_form(step_id="select", data_schema=data_schema)
 main
