"""Config flow for the Satel integration."""

from __future__ import annotations

import asyncio
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from . import SatelHub
from .const import (
    DOMAIN,
    DEFAULT_HOST,
    DEFAULT_PORT,
    CONF_CODE,
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

_LOGGER = logging.getLogger(__name__)


class SatelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Satel."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step of the flow."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._port = user_input[CONF_PORT]
            self._user_code = None
            self._encryption_key = None
            self._encoding = DEFAULT_ENCODING
            self._update_interval = DEFAULT_UPDATE_INTERVAL
            self._timeout = DEFAULT_TIMEOUT
            self._reconnect_delay = DEFAULT_RECONNECT_DELAY
            self._encryption_method = DEFAULT_ENCRYPTION_METHOD
            self._code = user_input[CONF_CODE]

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
            except RuntimeError:
                errors["base"] = "incompatible"
            except (asyncio.TimeoutError, ConnectionError, OSError):
                errors["base"] = "cannot_connect"
            except Exception as err:  # pylint: disable=broad-except
                errors["base"] = "unknown"
                _LOGGER.exception("Unexpected exception: %s", err)
            else:
                return await self.async_step_select()
            finally:
                await hub.async_close()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=DEFAULT_HOST): selector.TextSelector(),
                vol.Required(CONF_PORT, default=DEFAULT_PORT): selector.NumberSelector(),
                vol.Required(CONF_CODE): selector.TextSelector(),
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
                    "zones": user_input.get("zones", []),
                    "outputs": user_input.get("outputs", []),
                    "partitions": user_input.get("partitions", []),
                },
            )

        zone_values = [z["id"] for z in self._devices.get("zones", [])]
        zone_options = [
            selector.SelectOptionDict(value=z["id"], label=z["name"])
            for z in self._devices.get("zones", [])
        ]
        output_values = [o["id"] for o in self._devices.get("outputs", [])]
        output_options = [
            selector.SelectOptionDict(value=o["id"], label=o["name"])
            for o in self._devices.get("outputs", [])
        ]
        partition_values = [p["id"] for p in self._devices.get("partitions", [])]
        partition_options = [
            selector.SelectOptionDict(
                value=p["id"], label=p.get("name", p["id"])
            )
            for p in self._devices.get("partitions", [])
        ]

        data_schema = vol.Schema(
            {
                vol.Optional(
                    "partitions", default=partition_values
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=partition_options, multiple=True
                    )
                ),
                vol.Optional("zones", default=zone_values): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=zone_options, multiple=True
                    )
                ),
                vol.Optional(
                    "outputs", default=output_values
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=output_options, multiple=True
                    )
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

