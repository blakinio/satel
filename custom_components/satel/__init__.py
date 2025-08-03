"""Satel integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, DEFAULT_HOST, DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor", "binary_sensor", "switch"]


class SatelHub:
    """Simple Satel client communicating over TCP."""

    def __init__(
        self,
        host: str,
        port: int,
        *,
        connect_timeout: float = 10.0,
        reconnect_delay: float = 1.0,
        max_reconnect_delay: float = 30.0,
        max_retries: int = 5,
    ) -> None:
        self._host = host
        self._port = port
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._connect_timeout = connect_timeout
        self._reconnect_delay = reconnect_delay
        self._max_reconnect_delay = max_reconnect_delay
        self._max_retries = max_retries

    async def connect(self) -> None:
        """Connect to the Satel central."""
        _LOGGER.debug("Connecting to %s:%s", self._host, self._port)
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=self._connect_timeout,
            )
        except (asyncio.TimeoutError, OSError) as err:
            _LOGGER.error(
                "Failed to connect to %s:%s: %s", self._host, self._port, err
            )
            raise ConnectionError(err) from err

    async def send_command(self, command: str) -> str:
        """Send a command to the Satel central and return response."""
        if self._writer is None or self._writer.is_closing() or self._reader is None:
            await self._reconnect()

        for attempt in range(self._max_retries):
            try:
                _LOGGER.debug("Sending command: %s", command)
                self._writer.write((command + "\n").encode())
                await self._writer.drain()
                data = await asyncio.wait_for(
                    self._reader.readline(), timeout=self._connect_timeout
                )
                return data.decode().strip()
            except (ConnectionError, asyncio.TimeoutError, OSError) as err:
                _LOGGER.warning("Error communicating with Satel: %s", err)
                await self._reconnect()
        raise ConnectionError("Failed to communicate with Satel")

    async def _reconnect(self) -> None:
        """Attempt to reconnect with exponential backoff."""
        delay = self._reconnect_delay
        self._close_connection()
        for attempt in range(self._max_retries):
            _LOGGER.debug("Reconnecting in %s seconds", delay)
            await asyncio.sleep(delay)
            try:
                await self.connect()
                _LOGGER.info("Reconnected to Satel central")
                return
            except ConnectionError:
                delay = min(delay * 2, self._max_reconnect_delay)
        raise ConnectionError("Unable to reconnect to Satel")

    def _close_connection(self) -> None:
        """Close the current connection if open."""
        if self._writer is not None:
            self._writer.close()
            try:
                asyncio.create_task(self._writer.wait_closed())
            except Exception:  # pragma: no cover - best effort
                pass
        self._reader = None
        self._writer = None

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

    hub = SatelHub(host, port)
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
