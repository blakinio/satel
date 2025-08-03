"""Config flow for the Satel integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import DOMAIN, DEFAULT_HOST, DEFAULT_PORT


class SatelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Satel."""

    VERSION = 1

    async def async_step_user(self, user_input=None):  # type: ignore[override]
        if user_input is not None:
            return self.async_create_entry(title="Satel", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            }
        )
        return self.async_show_form(step_id="user", data_schema=data_schema)

