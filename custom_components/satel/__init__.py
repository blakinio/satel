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

 codex/extend-config_flow.py-for-credential-handling
 codex/extend-config_flow.py-for-credential-handling
=======
 main
from .const import (
    DOMAIN,
    DEFAULT_HOST,
    DEFAULT_PORT,
 codex/extend-config_flow.py-for-credential-handling
    CONF_ENCRYPTION_KEY,
    CONF_USER_CODE,
)
=======
from .const import DOMAIN, DEFAULT_HOST, DEFAULT_PORT, CONF_CODE
 main
=======
    CONF_CODE,
codex/add-configurable-timeout-to-send_command
    DEFAULT_TIMEOUT,
=======
    CONF_ENCODING,
    DEFAULT_ENCODING,
 main
)
 main

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = [
    "sensor",
    "binary_sensor",
    "switch",
    "alarm_control_panel",
]


class SatelHub:
    """Simple Satel client communicating over TCP."""

 codex/extend-satelhub-to-handle-network-errors
=======
 codex/extend-config_flow.py-for-credential-handling
 codex/extend-config_flow.py-for-credential-handling
 main
    def __init__(
        self,
        host: str,
        port: int,
codex/extend-satelhub-to-handle-network-errors
        *,
        connect_timeout: float = 10.0,
        reconnect_delay: float = 1.0,
        max_reconnect_delay: float = 30.0,
        max_retries: int = 5,
=======
        user_code: str | None = None,
        encryption_key: str | None = None,
 main
    ) -> None:
        self._host = host
        self._port = port
        self._user_code = user_code
        self._encryption_key = encryption_key
=======
    def __init__(self, host: str, port: int, code: str) -> None:
        self._host = host
        self._port = port
        self._code = code
=======
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
 main
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
 codex/extend-satelhub-to-handle-network-errors
        self._connect_timeout = connect_timeout
        self._reconnect_delay = reconnect_delay
        self._max_reconnect_delay = max_reconnect_delay
        self._max_retries = max_retries
=======
        self._lock = asyncio.Lock()

    @property
    def host(self) -> str:
        """Return the host address of the Satel hub."""
        return self._host
 main

    async def connect(self) -> None:
        """Connect to the Satel central."""
        _LOGGER.debug("Connecting to %s:%s", self._host, self._port)
 codex/extend-satelhub-to-handle-network-errors
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
=======
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
 codex/extend-config_flow.py-for-credential-handling
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
=======
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
 main

    async def async_close(self) -> None:
        """Close the connection to the Satel central."""
        if self._writer is not None:  # pragma: no cover - depends on network
            self._writer.close()
            await self._writer.wait_closed()
            self._writer = None
        self._reader = None
 main

 codex/update-get_status-and-send_command-methods
    async def send_command(self, command: str | bytes) -> bytes:
        """Send a command using Satel TCP framing.
 main

        The Satel protocol frames every payload with a start byte (0xFE),
        a length byte and a checksum.  ``command`` may either be a string or
        raw bytes representing the protocol command.  The payload returned
        by the central is returned without framing.
        """
=======
    async def send_command(self, command: str) -> str:
 main
main
        """Send a command to the Satel central and return response."""
 codex/extend-satelhub-to-handle-network-errors
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
=======
 codex/add-asyncio.lock-to-satelhub
        async with self._lock:
            if self._writer is None or self._reader is None:
                raise ConnectionError("Not connected to Satel central")

=======
 main
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

codex/update-get_status-and-send_command-methods
        payload = command.encode() if isinstance(command, str) else command

        frame = bytearray()
        frame.append(0xFE)
        frame.append(len(payload))
        frame.extend(payload)
        checksum = (0x100 - (sum(frame[1:]) % 0x100)) & 0xFF
        frame.append(checksum)

        _LOGGER.debug("Sending frame: %s", frame.hex())
        self._writer.write(frame)
        await self._writer.drain()

        start = await self._reader.readexactly(1)
        if start[0] != 0xFE:
            raise ConnectionError("Invalid start byte in response")

        length_byte = await self._reader.readexactly(1)
        length = length_byte[0]
        payload = await self._reader.readexactly(length)
        checksum_byte = await self._reader.readexactly(1)
        calc_checksum = (0x100 - ((length + sum(payload)) % 0x100)) & 0xFF
        if checksum_byte[0] != calc_checksum:
            raise ConnectionError("Checksum mismatch")

        _LOGGER.debug("Received payload: %s", payload.hex())
        return payload
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
 main
 main

    async def get_status(self) -> dict[str, Any]:
        """Retrieve and parse status information from the Satel central."""
        try:
 codex/update-get_status-and-send_command-methods
            # 0x7F is the "status" command in Satel protocol
            data = await self.send_command(b"\x7F")

            # Example layout: 4 bytes zones, 2 bytes partitions, 1 byte alarms
            zones_bits = int.from_bytes(data[0:4], "little")
            partitions_bits = int.from_bytes(data[4:6], "little")
            alarms_bits = data[6] if len(data) > 6 else 0

            zones = {
                zone + 1: bool(zones_bits & (1 << zone))
                for zone in range(32)
            }
            partitions = {
                part + 1: bool(partitions_bits & (1 << part))
                for part in range(16)
            }
            alarms = {
                "alarm": bool(alarms_bits & 0x01),
            }

            return {
                "zones": zones,
                "partitions": partitions,
                "alarms": alarms,
                "raw": "ALARM" if any(alarms.values()) else "OK",
            }
        except Exception as err:  # pragma: no cover - demonstration only
            _LOGGER.error("Failed to get status: %s", err)
            return {"zones": {}, "partitions": {}, "alarms": {}, "raw": "unknown"}
=======
            response = await self.send_command("STATUS")
            parsed: dict[str, Any] = {"zones": {}, "outputs": {}}
            for part in response.split(";"):
                if not part:
                    continue
                if part.startswith("Z"):
                    zone_id, state = part[1:].split("=")
                    parsed["zones"][zone_id] = state == "1"
                elif part.startswith("O"):
                    out_id, state = part[1:].split("=")
                    parsed["outputs"][out_id] = state == "1"
                elif part.startswith("ALARM"):
                    _, state = part.split("=")
                    parsed["alarm"] = state == "1"
            return parsed
        except Exception as err:  # pragma: no cover - demonstration only
            _LOGGER.error("Failed to get status: %s", err)
            return {"zones": {}, "outputs": {}, "alarm": False}

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
 codex/extend-config_flow.py-for-credential-handling
 
=======
 pr/44
 main
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
main


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Satel integration from YAML."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Satel from a config entry."""
    host = entry.data.get(CONF_HOST, DEFAULT_HOST)
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    user_code = entry.data.get(CONF_USER_CODE)
    encryption_key = entry.data.get(CONF_ENCRYPTION_KEY)

 codex/extend-config_flow.py-for-credential-handling
    hub = SatelHub(host, port, user_code, encryption_key)
    await hub.connect()
=======
    code = entry.data.get(CONF_CODE, "")
 codex/extend-config_flow.py-for-credential-handling
 main
=======
    encoding = entry.data.get(CONF_ENCODING, DEFAULT_ENCODING)
 main

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
