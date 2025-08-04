from unittest.mock import AsyncMock, MagicMock
import logging

import pytest
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.satel import SatelHub
from custom_components.satel.switch import SatelOutputSwitch


@pytest.mark.asyncio
async def test_turn_on_writes_state(hass):
    hub = SatelHub("host", 1234, "code")
    hub.send_command = AsyncMock()
    coordinator = DataUpdateCoordinator(
        hass,
        logging.getLogger(__name__),
        name="satel",
        update_method=AsyncMock(return_value={"outputs": {"1": "OFF"}}),
        config_entry=MockConfigEntry(domain="satel"),
    )
    switch = SatelOutputSwitch(hub, coordinator, "1", "Out")
    switch.async_write_ha_state = MagicMock()
    async def refresh():
        coordinator.data = {"outputs": {"1": "ON"}}
    switch.coordinator.async_request_refresh = AsyncMock(side_effect=refresh)
    coordinator.data = {"outputs": {"1": "OFF"}}

    await switch.async_turn_on()

    assert switch.is_on
    switch.async_write_ha_state.assert_called_once()
    switch.coordinator.async_request_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_turn_off_writes_state(hass):
    hub = SatelHub("host", 1234, "code")
    hub.send_command = AsyncMock()
    coordinator = DataUpdateCoordinator(
        hass,
        logging.getLogger(__name__),
        name="satel",
        update_method=AsyncMock(return_value={"outputs": {"1": "ON"}}),
        config_entry=MockConfigEntry(domain="satel"),
    )
    switch = SatelOutputSwitch(hub, coordinator, "1", "Out")
    switch._attr_is_on = True
    switch.async_write_ha_state = MagicMock()
    async def refresh_off():
        coordinator.data = {"outputs": {"1": "OFF"}}
    switch.coordinator.async_request_refresh = AsyncMock(side_effect=refresh_off)
    coordinator.data = {"outputs": {"1": "ON"}}

    await switch.async_turn_off()

    assert not switch.is_on
    switch.async_write_ha_state.assert_called_once()
    switch.coordinator.async_request_refresh.assert_called_once()
