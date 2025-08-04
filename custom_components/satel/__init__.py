"""Satel alarm integration using official ETHM-1 protocol."""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from datetime import timedelta
from typing import Any, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from satel_integra.satel_integra import AsyncSatel, AlarmState

from .const import (
    CONF_CODE,
    CONF_ENCODING,
    DEFAULT_ENCODING,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor", "binary_sensor", "switch", "alarm_control_panel"]


class SatelHub:
    """Wrapper around :class:`AsyncSatel` providing Home Assistant helpers."""

    def __init__(self, host: str, port: int, code: str | None = None) -> None:
        self._host = host
        self._port = port
        self._code = code or ""
        self._satel: AsyncSatel | None = None
        self._monitor_task: asyncio.Task | None = None
        self._coordinator: DataUpdateCoordinator | None = None
        self._state: dict[str, Any] = {"alarm": {}, "zones": {}, "outputs": {}}

    @property
    def host(self) -> str:  # pragma: no cover - trivial
        return self._host

    async def connect(self) -> None:
        """Create connection to the alarm using the official protocol."""
        loop = asyncio.get_event_loop()
        self._satel = AsyncSatel(self._host, self._port, loop)
        connected = await self._satel.connect()
        if not connected:
            raise ConnectionError("Unable to connect to Satel panel")

    async def start_monitoring(self, coordinator: DataUpdateCoordinator) -> None:
        """Start monitoring alarm events and push updates to coordinator."""

        if not self._satel:
            raise ConnectionError("Not connected")

        self._coordinator = coordinator

        def _schedule_update() -> None:
            if self._coordinator:
                data = {
                    "alarm": self._state["alarm"],
                    "zones": self._state["zones"].copy(),
                    "outputs": self._state["outputs"].copy(),
                }
                self._coordinator.async_set_updated_data(data)

        def zone_cb(status: dict[str, Any]) -> None:
            for zone, value in status.get("zones", {}).items():
                self._state["zones"][str(zone)] = "ON" if value else "OFF"
            _schedule_update()

        def output_cb(status: dict[str, Any]) -> None:
            for out, value in status.get("outputs", {}).items():
                self._state["outputs"][str(out)] = "ON" if value else "OFF"
            _schedule_update()

        def alarm_cb() -> None:
            if not self._satel:
                return
            states = self._satel.partition_states
            partitions: set[int] = set()
            for part_list in states.values():
                partitions.update(part_list)
            for part in partitions:
                key = str(part)
                if part in states.get(AlarmState.TRIGGERED, []) or part in states.get(
                    AlarmState.TRIGGERED_FIRE, []
                ):
                    self._state["alarm"][key] = "TRIGGERED"
                elif part in states.get(AlarmState.ENTRY_TIME, []) or part in states.get(
                    AlarmState.EXIT_COUNTDOWN_OVER_10, []
                ) or part in states.get(AlarmState.EXIT_COUNTDOWN_UNDER_10, []):
                    self._state["alarm"][key] = "PENDING"
                elif part in states.get(AlarmState.ARMED_MODE1, []):
                    self._state["alarm"][key] = "ARMED_HOME"
                elif part in states.get(AlarmState.ARMED_MODE2, []):
                    self._state["alarm"][key] = "ARMED_NIGHT"
                elif part in states.get(AlarmState.ARMED_MODE0, []):
                    self._state["alarm"][key] = "ARMED_AWAY"
                else:
                    self._state["alarm"][key] = "DISARMED"
            _schedule_update()

        self._monitor_task = asyncio.create_task(
            self._satel.monitor_status(
                alarm_status_callback=alarm_cb,
                zone_changed_callback=zone_cb,
                output_changed_callback=output_cb,
            )
        )

    async def async_close(self) -> None:
        """Stop monitoring and close connection."""
        if self._monitor_task:
            self._monitor_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._monitor_task
            self._monitor_task = None
        if self._satel:
            self._satel.close()
            self._satel = None

    async def get_overview(self) -> dict[str, Any]:
        """Return current known state."""
        return {
            "alarm": self._state["alarm"].copy(),
            "zones": self._state["zones"].copy(),
            "outputs": self._state["outputs"].copy(),
        }

    async def discover_devices(self) -> dict[str, list[dict[str, Any]]]:
        """Discovery is not available in protocol – return empty placeholders."""
        return {
            "zones": [],
            "outputs": [],
            "partitions": [
                {"id": str(i), "name": f"Partition {i}"} for i in range(1, 33)
            ],
        }

    async def set_output(self, output_id: str, state: bool) -> None:
        """Turn given output on or off."""
        if not self._satel:
            raise ConnectionError("Not connected")
        await self._satel.set_output(self._code, int(output_id), state)

    async def arm(self, partition: int | None = None) -> None:
        if not self._satel:
            raise ConnectionError("Not connected")
        parts = [partition] if partition else [1]
        await self._satel.arm(self._code, parts, mode=0)

    async def arm_home(self, partition: int | None = None) -> None:
        if not self._satel:
            raise ConnectionError("Not connected")
        parts = [partition] if partition else [1]
        await self._satel.arm(self._code, parts, mode=1)

    async def arm_night(self, partition: int | None = None) -> None:
        if not self._satel:
            raise ConnectionError("Not connected")
        parts = [partition] if partition else [1]
        await self._satel.arm(self._code, parts, mode=2)

    async def disarm(self, partition: int | None = None) -> None:
        if not self._satel:
            raise ConnectionError("Not connected")
        parts = [partition] if partition else [1]
        await self._satel.disarm(self._code, parts)

    async def disarm_partition(self, partition: int) -> None:
        await self.disarm(partition)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:  # pragma: no cover - YAML not supported
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host = entry.data.get(CONF_HOST, DEFAULT_HOST)
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    code = entry.data.get(CONF_CODE)

    hub = SatelHub(host, port, code)
    try:
        await hub.connect()
    except ConnectionError as err:
        await hub.async_close()
        raise ConfigEntryNotReady from err

    coordinator = DataUpdateCoordinator[
        dict[str, Any]
    ](
        hass,
        _LOGGER,
        name="satel",
        update_method=hub.get_overview,
        update_interval=timedelta(seconds=0),
        config_entry=entry,
    )
    await coordinator.async_config_entry_first_refresh()
    await hub.start_monitoring(coordinator)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "hub": hub,
        "devices": await hub.discover_devices(),
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        hub: SatelHub = data["hub"]
        await hub.async_close()
    return unload_ok

