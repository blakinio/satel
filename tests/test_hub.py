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

        zone_cb({"zones": {1: 1}})
        output_cb({"outputs": {2: 1}})
        satel.partition_states = {AlarmState.TRIGGERED: [1]}
        alarm_cb()

        assert coordinator.data["zones"]["1"] == "ON"
        assert coordinator.data["outputs"]["2"] == "ON"
        assert coordinator.data["alarm"]["1"] == "TRIGGERED"


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

