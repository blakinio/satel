"""Satel alarm integration."""

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
    CONF_ENCODING,
    DEFAULT_ENCODING,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor", "binary_sensor", "switch", "alarm_control_panel"]


class SatelHub:
    """Simple Satel client communicating over TCP."""

    def __init__(
        self,
        host: str,
        port: int,
        code: str = "",
        encoding: str = DEFAULT_ENCODING,
    ) -> None:
        self._host = host
        self._port = port
        self._code = code
        self._encoding = encoding
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()

    @property
    def host(self) -> str:
        """Return host address."""
        return self._host

    async def connect(self) -> None:
        """Open TCP connection to the panel."""
        self._reader, self._writer = await asyncio.open_connection(self._host, self._port)
        if self._code:
            await self.send_command(f"LOGIN {self._code}")

    async def send_command(self, command: str) -> str:
        """Send a command and return the response."""
        if self._reader is None or self._writer is None:
            raise ConnectionError("Not connected")
        async with self._lock:
            self._writer.write((command + "\n").encode(self._encoding))
            await self._writer.drain()
            response = await self._reader.readline()
        return response.decode(self._encoding).strip()

    async def get_status(self) -> dict[str, Any]:
        """Retrieve basic status information from the panel."""
        response = await self.send_command("STATUS")
        return {"raw": response}

    async def discover_devices(self) -> dict[str, list[dict[str, str]]]:
        """Return metadata for zones and outputs."""
        return {
            "zones": [{"id": "1", "name": "Zone 1"}],
            "outputs": [{"id": "1", "name": "Output 1"}],
        }

    async def async_close(self) -> None:
        """Close the TCP connection."""
        if self._writer is not None:
            self._writer.close()
            await self._writer.wait_closed()
        self._reader = None
        self._writer = None


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up integration via YAML (not supported)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Satel from a config entry."""
    host = entry.data.get(CONF_HOST, DEFAULT_HOST)
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    encoding = entry.data.get(CONF_ENCODING, DEFAULT_ENCODING)
    hub = SatelHub(host, port, encoding=encoding)
    await hub.connect()
    devices = await hub.discover_devices()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "hub": hub,
        "devices": devices,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        hub: SatelHub = data["hub"]
        await hub.async_close()
    return unload_ok

