"""Satel integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import (
    DOMAIN,
    DEFAULT_HOST,
    DEFAULT_PORT,
    CONF_ENCRYPTION_KEY,
    CONF_USER_CODE,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor", "binary_sensor", "switch"]


class SatelHub:
    """Simple Satel client communicating over TCP."""

    def __init__(
        self,
        host: str,
        port: int,
        user_code: str | None = None,
        encryption_key: str | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._user_code = user_code
        self._encryption_key = encryption_key
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    async def connect(self) -> None:
        """Connect to the Satel central."""
        _LOGGER.debug("Connecting to %s:%s", self._host, self._port)
        self._reader, self._writer = await asyncio.open_connection(
            self._host, self._port
        )
        if self._user_code or self._encryption_key:
            auth_parts: list[str] = []
            if self._user_code:
                auth_parts.append(self._user_code)
            if self._encryption_key:
                auth_parts.append(self._encryption_key)
            auth_cmd = "AUTH " + " ".join(auth_parts)
            _LOGGER.debug("Authenticating with Satel central")
            self._writer.write((auth_cmd + "\n").encode())
            await self._writer.drain()
            response = await self._reader.readline()
            if response.decode().strip().upper() != "OK":
                raise ConnectionError("Authentication failed")

    async def send_command(self, command: str) -> str:
        """Send a command to the Satel central and return response."""
        if self._writer is None or self._reader is None:
            raise ConnectionError("Not connected to Satel central")

        _LOGGER.debug("Sending command: %s", command)
        self._writer.write((command + "\n").encode())
        await self._writer.drain()
        data = await self._reader.readline()
        return data.decode().strip()

    async def get_status(self) -> dict[str, Any]:
        """Retrieve status from Satel central."""
        try:
            response = await self.send_command("STATUS")
            # In real implementation, parse response according to protocol
            return {"raw": response}
        except Exception as err:  # pragma: no cover - demonstration only
            _LOGGER.error("Failed to get status: %s", err)
            return {"raw": "unknown"}


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Satel integration from YAML."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Satel from a config entry."""
    host = entry.data.get(CONF_HOST, DEFAULT_HOST)
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    user_code = entry.data.get(CONF_USER_CODE)
    encryption_key = entry.data.get(CONF_ENCRYPTION_KEY)

    hub = SatelHub(host, port, user_code, encryption_key)
    await hub.connect()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hub: SatelHub = hass.data[DOMAIN].pop(entry.entry_id)
        if hub._writer is not None:  # pragma: no cover - graceful shutdown
            hub._writer.close()
            await hub._writer.wait_closed()
    return unload_ok
