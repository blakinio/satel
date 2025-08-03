"""Satel alarm integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

try:  # pragma: no cover - allows running tests without Home Assistant
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.const import CONF_HOST, CONF_PORT
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.typing import ConfigType
except ModuleNotFoundError:  # pragma: no cover - simple stubs
    ConfigEntry = HomeAssistant = object
    CONF_HOST = "host"
    CONF_PORT = "port"
    ConfigType = dict[str, Any]

from .const import (
    DOMAIN,
    DEFAULT_HOST,
    DEFAULT_PORT,
    CONF_CODE,
codex/add-configurable-timeout-to-send_command
    DEFAULT_TIMEOUT,
=======
    CONF_ENCODING,
    DEFAULT_ENCODING,
 main
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = [
    "sensor",
    "binary_sensor",
    "switch",
    "alarm_control_panel",
]


class SatelHub:
    """Simple Satel client communicating over TCP."""

 codex/add-configurable-timeout-to-send_command
    def __init__(self, host: str, port: int, code: str, timeout: float = DEFAULT_TIMEOUT) -> None:
        self._host = host
        self._port = port
        self._code = code
        self._timeout = timeout
=======
    def __init__(self, host: str, port: int, code: str, encoding: str = DEFAULT_ENCODING) -> None:
        self._host = host
        self._port = port
        self._code = code
        self._encoding = encoding
 main
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()

    @property
    def host(self) -> str:
        """Return the host address of the Satel hub."""
        return self._host

    async def connect(self) -> None:
        """Connect to the Satel central."""
        _LOGGER.debug("Connecting to %s:%s", self._host, self._port)
codex/wrap-asyncio.open_connection-in-try/except
        try:
            self._reader, self._writer = await asyncio.open_connection(
                self._host, self._port
            )
        except Exception as err:
            _LOGGER.error(
                "Failed to connect to %s:%s: %s", self._host, self._port, err
            )
            raise ConnectionError(
                f"Unable to connect to Satel at {self._host}:{self._port}"
            ) from err
=======
        self._reader, self._writer = await asyncio.open_connection(
            self._host, self._port
        )
        await self.send_command(f"LOGIN {self._code}")

 codex/add-configurable-timeout-to-send_command
    async def send_command(self, command: str, timeout: float | None = None) -> str:
=======
 codex/modify-satelhub.send_command-for-encoding
    async def send_command(self, command: str, encoding: str | None = None) -> str:
=======
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

    async def async_close(self) -> None:
        """Close the connection to the Satel central."""
        if self._writer is not None:  # pragma: no cover - depends on network
            self._writer.close()
            await self._writer.wait_closed()
            self._writer = None
        self._reader = None
 main

    async def send_command(self, command: str) -> str:
 main
main
        """Send a command to the Satel central and return response."""
 codex/add-asyncio.lock-to-satelhub
        async with self._lock:
            if self._writer is None or self._reader is None:
                raise ConnectionError("Not connected to Satel central")

=======
        if self._writer is None or self._reader is None:
            raise ConnectionError("Not connected to Satel central")
 codex/wrap-send_command-in-try/except-block
        try:
            _LOGGER.debug("Sending command: %s", command)
            self._writer.write((command + "\n").encode())
            await self._writer.drain()
            data = await self._reader.readline()
            return data.decode().strip()
        except (ConnectionError, ConnectionResetError) as err:
            _LOGGER.warning("Command %s failed: %s", command, err)
            if self._writer is not None:
                try:
                    self._writer.close()
                    await self._writer.wait_closed()
                except Exception:  # pragma: no cover - best effort to close
                    pass
                finally:
                    self._writer = None
                    self._reader = None
            await self.connect()
            try:
                _LOGGER.debug("Retrying command: %s", command)
                self._writer.write((command + "\n").encode())
                await self._writer.drain()
                data = await self._reader.readline()
                return data.decode().strip()
            except (ConnectionError, ConnectionResetError) as err:  # pragma: no cover - log and raise
                _LOGGER.warning("Retry for command %s failed: %s", command, err)
                raise
=======

 codex/add-configurable-timeout-to-send_command
        timeout = timeout if timeout is not None else self._timeout

        _LOGGER.debug("Sending command: %s", command)
        try:
            self._writer.write((command + "\n").encode())
            await asyncio.wait_for(self._writer.drain(), timeout)
            data = await asyncio.wait_for(self._reader.readline(), timeout)
        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout while sending command: %s", command)
            raise err
        return data.decode().strip()
=======
 codex/add-asyncio-lock-in-satelhub
        async with self._lock:
=======
 codex/implement-asyncio-lock-in-satelhub
        async with self._lock:
 main
 main
            _LOGGER.debug("Sending command: %s", command)
            self._writer.write((command + "\n").encode())
            await self._writer.drain()
            data = await self._reader.readline()
 codex/add-asyncio-lock-in-satelhub
        return data.decode().strip()
=======
 codex/add-asyncio.lock-to-satelhub
            return data.decode().strip()
=======
        return data.decode().strip()
=======
        used_encoding = encoding or self._encoding or DEFAULT_ENCODING
        _LOGGER.debug("Sending command: %s", command)
 codex/modify-satelhub.send_command-for-encoding
        self._writer.write((command + "\n").encode())
        await self._writer.drain()
        data = await self._reader.readline()
        decoded = data.decode(used_encoding, errors="replace").strip()
        if "\ufffd" in decoded:
            _LOGGER.warning(
                "Response decoding with %s failed: %s", used_encoding, data
            )
        return decoded
=======
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
 main
 main
 main
 main
 main
main

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

        default_metadata = {
            "zones": [{"id": "1", "name": "Zone 1"}],
            "outputs": [{"id": "1", "name": "Output 1"}],
        }

        parts = response.split("|", 1)
        if len(parts) != 2:
            _LOGGER.error("Unexpected LIST response: %s", response)
            return default_metadata

        zones_part, outputs_part = parts
        try:
            for item in zones_part.split(","):
                if not item:
                    continue
                if "=" not in item:
                    _LOGGER.warning("Invalid zone entry: %s", item)
                    continue
                zone_id, name = item.split("=", 1)
                metadata["zones"].append({"id": zone_id, "name": name})
            for item in outputs_part.split(","):
                if not item:
                    continue
                if "=" not in item:
                    _LOGGER.warning("Invalid output entry: %s", item)
                    continue
                out_id, name = item.split("=", 1)
                metadata["outputs"].append({"id": out_id, "name": name})
        except Exception as err:  # pragma: no cover - demonstration only
 HEAD
            _LOGGER.error("Device discovery failed: %s (response: %s)", err, response)
            metadata = {
                "zones": [{"id": "1", "name": "Zone 1"}],
                "outputs": [{"id": "1", "name": "Output 1"}],
            }
=======
            _LOGGER.error("Device discovery failed: %s", err)
            metadata = default_metadata
 pr/44
        return metadata

 codex/refactor-async_unload_entry-to-call-async_close
    async def async_close(self) -> None:
        """Close connection to the Satel central."""
        if self._writer is not None:  # pragma: no cover - graceful shutdown
            self._writer.close()
            await self._writer.wait_closed()
            self._writer = None
            self._reader = None
=======
    async def arm(self) -> None:
        """Arm the alarm."""
        await self.send_command("ARM")

    async def disarm(self) -> None:
        """Disarm the alarm."""
        await self.send_command("DISARM")
 main


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Satel integration from YAML."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Satel from a config entry."""
    host = entry.data.get(CONF_HOST, DEFAULT_HOST)
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)

    code = entry.data.get(CONF_CODE, "")
    encoding = entry.data.get(CONF_ENCODING, DEFAULT_ENCODING)

    hub = SatelHub(host, port, code, encoding)
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
codex/add-async_close-method-to-satelhub
        hub: SatelHub = hass.data[DOMAIN].pop(entry.entry_id)
        await hub.async_close()
=======
 codex/refactor-async_unload_entry-to-call-async_close
        data = hass.data[DOMAIN].pop(entry.entry_id)
        hub = data["hub"]
        await hub.async_close()
=======
 codex/refactor-async_unload_entry-to-retrieve-hub
        data = hass.data[DOMAIN].pop(entry.entry_id)
        hub: SatelHub = data["hub"]
=======
 codex/update-async_unload_entry-to-extract-hub
        entry_data = hass.data[DOMAIN].pop(entry.entry_id, {})
        hub: SatelHub = entry_data["hub"]
        if writer := hub._writer:  # pragma: no cover - graceful shutdown
            writer.close()
            await writer.wait_closed()
=======
        data = hass.data[DOMAIN].pop(entry.entry_id)
        hub: SatelHub = data["hub"]
        # devices metadata removed from hass.data with the pop above
 main
        if hub._writer is not None:  # pragma: no cover - graceful shutdown
            hub._writer.close()
            await hub._writer.wait_closed()
        hub._writer = None
        hub._reader = None
 main
 main
 main
    return unload_ok
