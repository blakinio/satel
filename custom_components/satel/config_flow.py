"""Config flow for Satel integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

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


class SatelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Satel."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
 codex/add-translations-for-custom-components
            hub = SatelHub(user_input[CONF_HOST], user_input[CONF_PORT])
            try:
                await hub.connect()
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"Satel {user_input[CONF_HOST]}", data=user_input
                )
=======
            self._host = user_input[CONF_HOST]
            self._port = user_input[CONF_PORT]
 codex/handle-network-errors-in-config_flow
            hub = SatelHub(self._host, self._port)
            try:
                await hub.connect()
                self._devices = await hub.discover_devices()
codex/add-error-handling-in-async_step_user
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "cannot_connect"
            else:
                return await self.async_step_select()
=======
            except (OSError, ConnectionError):
                errors["base"] = "cannot_connect"
            else:
                return await self.async_step_select()
=======
            self._code = user_input[CONF_CODE]
 codex/handle-connection-errors-in-config-flow
            hub = SatelHub(self._host, self._port, self._code)
            try:
                await hub.connect()
                self._devices = await hub.discover_devices()
            except ConnectionError:
                errors["base"] = "cannot_connect"
            else:
                return await self.async_step_select()
=======
            self._encoding = user_input.get(CONF_ENCODING, DEFAULT_ENCODING)
            hub = SatelHub(self._host, self._port, self._code, self._encoding)
            await hub.connect()
            self._devices = await hub.discover_devices()
            return await self.async_step_select()
codex/add-translations-for-custom-components
 main
=======
main main
main
 main

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
 codex/extend-config_flow.py-for-credential-handling
                vol.Optional(CONF_USER_CODE): str,
                vol.Optional(CONF_ENCRYPTION_KEY): str,
=======
                vol.Required(CONF_CODE): str,
 codex/extend-config_flow.py-for-credential-handling
 main
=======
                vol.Optional(CONF_ENCODING, default=DEFAULT_ENCODING): str,
 main
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
                vol.Optional("zones", default=list(zone_options)): cv.multi_select(zone_options),
                vol.Optional("outputs", default=list(output_options)): cv.multi_select(output_options),
            }
        )
        return self.async_show_form(step_id="select", data_schema=data_schema)
