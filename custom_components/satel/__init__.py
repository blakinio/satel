"""Satel integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, DEFAULT_HOST, DEFAULT_PORT, CONF_CODE

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor", "binary_sensor", "switch"]


class SatelHub:
    """Simple Satel client communicating over TCP."""

    def __init__(self, host: str, port: int, code: str) -> None:
        self._host = host
        self._port = port
        self._code = code
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    @property
    def host(self) -> str:
        """Return the host address of the Satel hub."""
        return self._host

    async def connect(self) -> None:
        """Connect to the Satel central."""
        _LOGGER.debug("Connecting to %s:%s", self._host, self._port)
        self._reader, self._writer = await asyncio.open_connection(
            self._host, self._port
        )
        await self.send_command(f"LOGIN {self._code}")

    async def _close_connection(self) -> None:
        """Close the current TCP connection."""
        if self._writer is not None:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:  # pragma: no cover - best effort
                pass
        self._reader = None
        self._writer = None

    async def send_command(self, command: str) -> str:
        """Send a command to the Satel central and return response."""
        if self._writer is None or self._reader is None:
            raise ConnectionError("Not connected to Satel central")

        _LOGGER.debug("Sending command: %s", command)
        try:
            self._writer.write((command + "\n").encode())
            await self._writer.drain()
            data = await self._reader.readline()
            if not data:
                raise ConnectionResetError("No data received")
            return data.decode().strip()
        except (ConnectionResetError, BrokenPipeError, OSError, asyncio.IncompleteReadError) as err:
            _LOGGER.warning("Connection error while sending '%s': %s", command, err)
            await self._close_connection()
            try:
                await self.connect()
            except Exception as conn_err:
                raise ConnectionError("Failed to reconnect to Satel central") from conn_err
            try:
                self._writer.write((command + "\n").encode())
                await self._writer.drain()
                data = await self._reader.readline()
                if not data:
                    raise ConnectionError("No response after reconnection")
                return data.decode().strip()
            except Exception as err2:
                await self._close_connection()
                raise ConnectionError(
                    "Failed to send command after reconnection"
                ) from err2

    async def get_status(self) -> dict[str, Any]:
        """Retrieve status from Satel central."""
        try:
            response = await self.send_command("STATUS")
            # In real implementation, parse response according to protocol
            return {"raw": response}
        except Exception as err:  # pragma: no cover - demonstration only
            _LOGGER.error("Failed to get status: %s", err)
            return {"raw": "unknown"}

    async def discover_devices(self) -> dict[str, list[dict[str, Any]]]:
        """Discover zones and outputs available on the panel."""
        metadata: dict[str, list[dict[str, Any]]] = {"zones": [], "outputs": []}
        try:
            response = await self.send_command("LIST")
        except ConnectionError as err:
            _LOGGER.warning("LIST command failed (%s). Attempting reconnection", err)
            try:
                await self.connect()
                response = await self.send_command("LIST")
            except Exception as err:
                _LOGGER.error("Device discovery failed after reconnection: %s", err)
                return {
                    "zones": [{"id": "1", "name": "Zone 1"}],
                    "outputs": [{"id": "1", "name": "Output 1"}],
                }
        except Exception as err:  # pragma: no cover - demonstration only
            _LOGGER.error("Device discovery failed: %s", err)
            return {
                "zones": [{"id": "1", "name": "Zone 1"}],
                "outputs": [{"id": "1", "name": "Output 1"}],
            }

        try:
            zones_part, outputs_part = response.split("|")
            for item in zones_part.split(","):
                if not item:
                    continue
                zone_id, name = item.split("=", 1)
                metadata["zones"].append({"id": zone_id, "name": name})
            for item in outputs_part.split(","):
                if not item:
                    continue
                out_id, name = item.split("=", 1)
                metadata["outputs"].append({"id": out_id, "name": name})
        except Exception as err:  # pragma: no cover - demonstration only
            _LOGGER.error("Device discovery failed: %s", err)
            metadata = {
                "zones": [{"id": "1", "name": "Zone 1"}],
                "outputs": [{"id": "1", "name": "Output 1"}],
            }
        return metadata


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Satel integration from YAML."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Satel from a config entry."""
    host = entry.data.get(CONF_HOST, DEFAULT_HOST)
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)

    code = entry.data.get(CONF_CODE, "")

    hub = SatelHub(host, port, code)
    await hub.connect()
    devices = await hub.discover_devices()
    selected_zones = entry.data.get("zones")
    selected_outputs = entry.data.get("outputs")
    if selected_zones is not None:
        devices["zones"] = [z for z in devices["zones"] if z["id"] in selected_zones]
    if selected_outputs is not None:
        devices["outputs"] = [o for o in devices["outputs"] if o["id"] in selected_outputs]

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
        hub: SatelHub = hass.data[DOMAIN].pop(entry.entry_id)
        if hub._writer is not None:  # pragma: no cover - graceful shutdown
            hub._writer.close()
            await hub._writer.wait_closed()
    return unload_ok
