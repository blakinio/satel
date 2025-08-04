"""Config flow for the Satel integration."""

from __future__ import annotations

import asyncio
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
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    CONF_TIMEOUT,
    DEFAULT_TIMEOUT,
    CONF_RECONNECT_DELAY,
    DEFAULT_RECONNECT_DELAY,
    CONF_ENCRYPTION_METHOD,
    DEFAULT_ENCRYPTION_METHOD,
    ENCRYPTION_METHODS,
)


class SatelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Satel."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step of the flow."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._port = user_input[CONF_PORT]
            self._code = user_input.get(CONF_CODE)
            self._user_code = user_input.get(CONF_USER_CODE)
            self._encryption_key = user_input.get(CONF_ENCRYPTION_KEY)
            self._encoding = user_input.get(CONF_ENCODING, DEFAULT_ENCODING)
            self._update_interval = user_input.get(
                CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
            )
            self._timeout = user_input.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
            self._reconnect_delay = user_input.get(
                CONF_RECONNECT_DELAY, DEFAULT_RECONNECT_DELAY
            )
            self._encryption_method = user_input.get(
                CONF_ENCRYPTION_METHOD, DEFAULT_ENCRYPTION_METHOD
            )

            await self.async_set_unique_id(self._host)
            self._abort_if_unique_id_configured()

            hub = SatelHub(
                self._host,
                self._port,
                self._code,
                user_code=self._user_code,
                encryption_key=self._encryption_key,
                encoding=self._encoding,
                update_interval=self._update_interval,
                timeout=self._timeout,
                reconnect_delay=self._reconnect_delay,
                encryption_method=self._encryption_method,
            )
            try:
                await hub.connect()
                self._devices = await hub.discover_devices()
            except (asyncio.TimeoutError, ConnectionError, OSError):
                errors["base"] = "cannot_connect"
            else:
                return await self.async_step_select()
            finally:
                await hub.async_close()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(CONF_CODE): str,
                vol.Optional(CONF_USER_CODE): str,
                vol.Optional(CONF_ENCRYPTION_KEY): str,
                vol.Optional(CONF_ENCODING, default=DEFAULT_ENCODING): str,
                vol.Optional(
                    CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                ): int,
                vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): int,
                vol.Optional(
                    CONF_RECONNECT_DELAY, default=DEFAULT_RECONNECT_DELAY
                ): int,
                vol.Optional(
                    CONF_ENCRYPTION_METHOD, default=DEFAULT_ENCRYPTION_METHOD
                ): vol.In(ENCRYPTION_METHODS),
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
                    CONF_USER_CODE: self._user_code,
                    CONF_ENCRYPTION_KEY: self._encryption_key,
                    CONF_ENCODING: self._encoding,
                    CONF_UPDATE_INTERVAL: self._update_interval,
                    CONF_TIMEOUT: self._timeout,
                    CONF_RECONNECT_DELAY: self._reconnect_delay,
                    CONF_ENCRYPTION_METHOD: self._encryption_method,
                    "zones": user_input.get("zones", []),
                    "outputs": user_input.get("outputs", []),
                    "partitions": user_input.get("partitions", []),
                },
            )

        zone_options = {z["id"]: z["name"] for z in self._devices.get("zones", [])}
        output_options = {
            o["id"]: o["name"] for o in self._devices.get("outputs", [])
        }
        partition_options = {
            p["id"]: p.get("name", p["id"])
            for p in self._devices.get("partitions", [])
        }

        data_schema = vol.Schema(
            {
                vol.Optional(
                    "partitions", default=list(partition_options)
                ): cv.multi_select(partition_options),
                vol.Optional("zones", default=list(zone_options)): cv.multi_select(
                    zone_options
                ),
                vol.Optional("outputs", default=list(output_options)): cv.multi_select(
                    output_options
                ),
            }
        )
        return self.async_show_form(step_id="select", data_schema=data_schema)

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "SatelOptionsFlow":
        """Return options flow handler."""
        return SatelOptionsFlow(config_entry)


class SatelOptionsFlow(config_entries.OptionsFlow):
    """Handle Satel options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Manage Satel options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = {**self._config_entry.data, **self._config_entry.options}
        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_UPDATE_INTERVAL,
                    default=data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                ): int,
                vol.Optional(
                    CONF_TIMEOUT, default=data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
                ): int,
                vol.Optional(
                    CONF_RECONNECT_DELAY,
                    default=data.get(CONF_RECONNECT_DELAY, DEFAULT_RECONNECT_DELAY),
                ): int,
                vol.Optional(
                    CONF_ENCRYPTION_METHOD,
                    default=data.get(
                        CONF_ENCRYPTION_METHOD, DEFAULT_ENCRYPTION_METHOD
                    ),
                ): vol.In(ENCRYPTION_METHODS),
            }
        )
        return self.async_show_form(step_id="init", data_schema=data_schema)

