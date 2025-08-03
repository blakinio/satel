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

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    async def connect(self) -> None:
        """Connect to the Satel central."""
        _LOGGER.debug("Connecting to %s:%s", self._host, self._port)
        self._reader, self._writer = await asyncio.open_connection(
            self._host, self._port
        )

    async def send_command(self, command: str | bytes) -> bytes:
        """Send a command using Satel TCP framing.

        The Satel protocol frames every payload with a start byte (0xFE),
        a length byte and a checksum.  ``command`` may either be a string or
        raw bytes representing the protocol command.  The payload returned
        by the central is returned without framing.
        """
        if self._writer is None or self._reader is None:
            raise ConnectionError("Not connected to Satel central")

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

    async def get_status(self) -> dict[str, Any]:
        """Retrieve and parse status information from the Satel central."""
        try:
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
