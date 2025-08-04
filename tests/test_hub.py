import logging
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.satel import SatelHub
from satel_integra.satel_integra import AlarmState


@pytest.mark.asyncio
async def test_connect_failure():
    satel = AsyncMock()
    satel.connect = AsyncMock(return_value=False)
    with patch("custom_components.satel.AsyncSatel", return_value=satel):
        hub = SatelHub("host", 1234, "code")
        with pytest.raises(ConnectionError):
            await hub.connect()


@pytest.mark.asyncio
async def test_monitoring_updates_state(hass):
    satel = AsyncMock()
    satel.connect = AsyncMock(return_value=True)
    satel.monitor_status = AsyncMock()
    satel.partition_states = {}
    with patch("custom_components.satel.AsyncSatel", return_value=satel):
        hub = SatelHub("host", 1234, "code")
        await hub.connect()
        coordinator = DataUpdateCoordinator(
            hass,
            logging.getLogger(__name__),
            name="satel",
            update_method=hub.get_overview,
            config_entry=MockConfigEntry(domain="satel"),
        )
        await coordinator.async_refresh()
        await hub.start_monitoring(coordinator)

        zone_cb = satel.monitor_status.call_args.kwargs["zone_changed_callback"]
        output_cb = satel.monitor_status.call_args.kwargs["output_changed_callback"]
        alarm_cb = satel.monitor_status.call_args.kwargs["alarm_status_callback"]

        zone_cb(
            {
                "zones": {1: 1},
                "tamper": {1: 1},
                "troubles": {1: 0},
                "bypass": {1: 1},
                "alarm_memory": {1: 0},
            }
        )
        output_cb({"outputs": {2: 1}})
        satel.partition_states = {AlarmState.TRIGGERED: [1]}
        alarm_cb()

        assert coordinator.data["zones"]["1"] == "ON"
        assert coordinator.data["outputs"]["2"] == "ON"
        assert coordinator.data["alarm"]["1"] == "TRIGGERED"
        assert coordinator.data["tamper"]["1"] == "ON"
        assert coordinator.data["bypass"]["1"] == "ON"
        assert coordinator.data["troubles"]["1"] == "OFF"


@pytest.mark.asyncio
async def test_partition_commands():
    satel = AsyncMock()
    satel.connect = AsyncMock(return_value=True)
    with patch("custom_components.satel.AsyncSatel", return_value=satel):
        hub = SatelHub("host", 1234, "code")
        await hub.connect()
        satel.arm = AsyncMock()
        satel.disarm = AsyncMock()
        await hub.arm_home(2)
        satel.arm.assert_awaited_with("code", [2], mode=1)
        await hub.arm_night(3)
        satel.arm.assert_awaited_with("code", [3], mode=2)
        await hub.disarm_partition(4)
        satel.disarm.assert_awaited_with("code", [4])


@pytest.mark.asyncio
async def test_discover_devices_reads_names():
    """Ensure the hub fetches zone and output names from the panel."""
    satel = AsyncMock()
    satel.get_zone_names = AsyncMock(return_value={1: "Zone 1"})
    satel.get_output_names = AsyncMock(return_value={2: "Out 2"})

    hub = SatelHub("host", 1234, "code")
    hub._satel = satel  # pretend already connected
    hub.set_monitored_zones([])
    hub.set_monitored_outputs([])

    devices = await hub.discover_devices()

    assert devices["zones"] == [{"id": "1", "name": "Zone 1"}]
    assert devices["outputs"] == [{"id": "2", "name": "Out 2"}]
    assert hub.monitored_zones == [1]
    assert hub.monitored_outputs == [2]

