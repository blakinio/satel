"""Satel alarm integration."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    DOMAIN,
    DEFAULT_HOST,
    DEFAULT_PORT,
    CONF_CODE,
    CONF_USER_CODE,
    CONF_ENCRYPTION_KEY,
    CONF_ENCODING,
    DEFAULT_ENCODING,
    DEFAULT_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor", "binary_sensor", "switch", "alarm_control_panel"]


class SatelHub:
    """Client for communicating with a Satel alarm panel over TCP."""

    def __init__(
        self,
        host: str,
        port: int,
        code: str | None = None,
        *,
        user_code: str | None = None,
        encryption_key: str | None = None,
        encoding: str = DEFAULT_ENCODING,
        timeout: float = DEFAULT_TIMEOUT,
        connect_timeout: float = 10.0,
        reconnect_delay: float = 1.0,
        max_reconnect_delay: float = 30.0,
        max_retries: int = 5,
    ) -> None:
        self._host = host
        self._port = port
        self._code = code
        self._user_code = user_code
        self._encryption_key = encryption_key
        self._encoding = encoding
        self._timeout = timeout
        self._connect_timeout = connect_timeout
        self._reconnect_delay = reconnect_delay
        self._max_reconnect_delay = max_reconnect_delay
        self._max_retries = max_retries
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()

    @property
    def host(self) -> str:
        """Return host address."""
        return self._host

    async def connect(self) -> None:
        """Connect to the Satel central."""
        _LOGGER.debug("Connecting to %s:%s", self._host, self._port)
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=self._connect_timeout,
            )
        except (asyncio.TimeoutError, OSError) as err:  # pragma: no cover - network error
            _LOGGER.error(
                "Failed to connect to %s:%s: %s", self._host, self._port, err
            )
            raise ConnectionError(err) from err

        if self._user_code or self._encryption_key:
            auth_parts: list[str] = []
            if self._user_code:
                auth_parts.append(self._user_code)
            if self._encryption_key:
                auth_parts.append(self._encryption_key)
            auth_cmd = "AUTH " + " ".join(auth_parts)
            _LOGGER.debug("Authenticating with Satel central")
            self._writer.write((auth_cmd + "\n").encode(self._encoding))
            await self._writer.drain()
            response = await self._reader.readline()
            if response.decode(self._encoding).strip().upper() != "OK":
                await self._close_connection()
                raise ConnectionError("Authentication failed")

        if self._code:
            response = await self.send_command(f"LOGIN {self._code}")
            if response.strip().upper() != "OK":
                await self._close_connection()
                raise ConnectionError("Login failed")

    async def send_command(
        self,
        command: str,
        *,
        timeout: float | None = None,
        encoding: str | None = None,
    ) -> str:
        """Send a command to the Satel central and return response."""
        used_timeout = timeout or self._timeout
        used_encoding = encoding or self._encoding

        async with self._lock:
            if self._writer is None or self._reader is None:
                raise ConnectionError("Not connected to Satel central")

            for attempt in range(2):
                try:
                    _LOGGER.debug("Sending command: %s", command)
                    self._writer.write((command + "\n").encode(used_encoding))
                    await asyncio.wait_for(self._writer.drain(), used_timeout)
                    data = await asyncio.wait_for(
                        self._reader.readline(), used_timeout
                    )
                    if not data:
                        raise ConnectionError("No data received")
                    return data.decode(used_encoding).strip()
                except asyncio.TimeoutError:
                    _LOGGER.error("Timeout while sending command: %s", command)
                    raise
                except (
                    ConnectionResetError,
                    BrokenPipeError,
                    OSError,
                    asyncio.IncompleteReadError,
                ) as err:
                    _LOGGER.warning(
                        "Connection error while sending '%s': %s", command, err
                    )
                    if attempt == 0:
                        try:
                            await self._reconnect()
                        except ConnectionError as conn_err:
                            raise ConnectionError(
                                "Failed to reconnect to Satel central"
                            ) from conn_err
                        continue
                    raise ConnectionError(
                        "Failed to send command after reconnection"
                    ) from err

    async def _reconnect(self) -> None:
        """Attempt to reconnect with exponential backoff."""
        await self._close_connection()
        delay = self._reconnect_delay
        for _ in range(self._max_retries):
            _LOGGER.debug("Reconnecting in %s seconds", delay)
            await asyncio.sleep(delay)
            try:
                await self.connect()
                _LOGGER.info("Reconnected to Satel central")
                return
            except ConnectionError:
                delay = min(delay * 2, self._max_reconnect_delay)
        raise ConnectionError("Unable to reconnect to Satel")

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
        await self._close_connection()

    async def get_status(self) -> dict[str, Any]:
        """Retrieve status information from the Satel central."""
        try:
            response = await self.send_command("STATUS")
            return {"raw": response}
        except Exception as err:  # pragma: no cover - demonstration only
            _LOGGER.error("Failed to get status: %s", err)
            return {"raw": "unknown"}

    async def get_overview(self) -> dict[str, Any]:
        """Get overall alarm, zone and output states in a single request."""
        try:
            response = await self.send_command("STATE")
        except ConnectionError as err:
            raise err
        parts = response.split("|", 2)
        if len(parts) != 3:
            raise UpdateFailed(f"Unexpected STATE response: {response}")
        alarm_part, zones_part, outputs_part = parts
        zones: dict[str, str] = {}
        outputs: dict[str, str] = {}
        for item in zones_part.split(","):
            if not item or "=" not in item:
                continue
            zone_id, state = item.split("=", 1)
            zones[zone_id] = state
        for item in outputs_part.split(","):
            if not item or "=" not in item:
                continue
            out_id, state = item.split("=", 1)
            outputs[out_id] = state
        return {"alarm": alarm_part, "zones": zones, "outputs": outputs}

    async def discover_devices(self) -> dict[str, list[dict[str, Any]]]:
        """Discover zones and outputs available on the panel."""
        metadata: dict[str, list[dict[str, Any]]] = {"zones": [], "outputs": []}
        try:
            response = await self.send_command("LIST")
        except Exception as err:  # pragma: no cover - demonstration only
            _LOGGER.error("Device discovery failed: %s", err)
            return metadata

        parts = response.split("|", 1)
        if len(parts) != 2:
            _LOGGER.error("Unexpected LIST response: %s", response)
            return metadata
        zones_part, outputs_part = parts
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
        return metadata

    async def arm(self) -> None:
        """Arm the alarm."""
        await self.send_command("ARM")

    async def disarm(self) -> None:
        """Disarm the alarm."""
        await self.send_command("DISARM")


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up integration via YAML (not supported)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Satel from a config entry."""
    host = entry.data.get(CONF_HOST, DEFAULT_HOST)
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    code = entry.data.get(CONF_CODE)
    user_code = entry.data.get(CONF_USER_CODE)
    encryption_key = entry.data.get(CONF_ENCRYPTION_KEY)
    encoding = entry.data.get(CONF_ENCODING, DEFAULT_ENCODING)

    hub = SatelHub(
        host,
        port,
        code,
        user_code=user_code,
        encryption_key=encryption_key,
        encoding=encoding,
    )
    try:
        await hub.connect()
    except ConnectionError as err:
        await hub.async_close()
        raise ConfigEntryNotReady from err

    try:
        devices = await hub.discover_devices()
    except Exception:  # pragma: no cover - discovery is best effort
        devices = {"zones": [], "outputs": []}

    coordinator = DataUpdateCoordinator[
        dict[str, Any]
    ](
        hass,
        _LOGGER,
        name="satel",
        update_method=hub.get_overview,
        update_interval=timedelta(seconds=30),
        config_entry=entry,
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "hub": hub,
        "devices": devices,
        "coordinator": coordinator,
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

