import logging
from unittest.mock import AsyncMock

import pytest
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.satel import SatelHub
from custom_components.satel.alarm_control_panel import SatelAlarmPanel


@pytest.mark.asyncio
async def test_alarm_panel_states_and_commands(hass):
    hub = SatelHub("host", 1234, "code")
    hub.arm = AsyncMock()
    hub.arm_home = AsyncMock()
    hub.arm_night = AsyncMock()
    hub.disarm_partition = AsyncMock()
    coordinator = DataUpdateCoordinator(
        hass,
        logging.getLogger(__name__),
        name="satel",
        update_method=AsyncMock(return_value={}),
        config_entry=MockConfigEntry(domain="satel"),
    )
    coordinator.data = {"alarm": {"1": "DISARMED"}}
    panel = SatelAlarmPanel(hub, coordinator, "1")

    await panel.async_alarm_arm_away()
    hub.arm.assert_awaited_with("1")
    await panel.async_alarm_arm_home()
    hub.arm_home.assert_awaited_with("1")
    await panel.async_alarm_arm_night()
    hub.arm_night.assert_awaited_with("1")
    await panel.async_alarm_disarm()
    hub.disarm_partition.assert_awaited_with("1")

    coordinator.data = {"alarm": {"1": "ARMED_HOME"}}
    assert panel.state == STATE_ALARM_ARMED_HOME
    coordinator.data = {"alarm": {"1": "ARMED_NIGHT"}}
    assert panel.state == STATE_ALARM_ARMED_NIGHT
    coordinator.data = {"alarm": {"1": "ARMED_AWAY"}}
    assert panel.state == STATE_ALARM_ARMED_AWAY
    coordinator.data = {"alarm": {"1": "PENDING"}}
    assert panel.state == STATE_ALARM_PENDING
    coordinator.data = {"alarm": {"1": "TRIGGERED"}}
    assert panel.state == STATE_ALARM_TRIGGERED
    coordinator.data = {"alarm": {"1": "DISARMED"}}
    assert panel.state == STATE_ALARM_DISARMED
