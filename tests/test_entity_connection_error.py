from unittest.mock import AsyncMock, MagicMock
import logging

import pytest
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.satel import SatelHub
from custom_components.satel.binary_sensor import SatelZoneBinarySensor
from custom_components.satel.sensor import SatelZoneSensor
from custom_components.satel.switch import SatelOutputSwitch


@pytest.mark.asyncio
async def test_binary_sensor_unavailable_on_coordinator_error(hass):
    hub = SatelHub("host", 1234, "code")
    coordinator = DataUpdateCoordinator(
        hass,
        logging.getLogger(__name__),
        name="satel",
        update_method=AsyncMock(side_effect=ConnectionError),
        config_entry=MockConfigEntry(domain="satel"),
    )
    entity = SatelZoneBinarySensor(hub, coordinator, "1", "Zone")
    await coordinator.async_refresh()
    assert not entity.available


@pytest.mark.asyncio
async def test_sensor_unavailable_on_coordinator_error(hass):
    hub = SatelHub("host", 1234, "code")
    coordinator = DataUpdateCoordinator(
        hass,
        logging.getLogger(__name__),
        name="satel",
        update_method=AsyncMock(side_effect=ConnectionError),
        config_entry=MockConfigEntry(domain="satel"),
    )
    entity = SatelZoneSensor(hub, coordinator, "1", "Zone")
    await coordinator.async_refresh()
    assert not entity.available


@pytest.mark.asyncio
async def test_switch_unavailable_on_coordinator_error(hass):
    hub = SatelHub("host", 1234, "code")
    coordinator = DataUpdateCoordinator(
        hass,
        logging.getLogger(__name__),
        name="satel",
        update_method=AsyncMock(side_effect=ConnectionError),
        config_entry=MockConfigEntry(domain="satel"),
    )
    entity = SatelOutputSwitch(hub, coordinator, "1", "Out")
    await coordinator.async_refresh()
    assert not entity.available


@pytest.mark.asyncio
async def test_switch_turn_on_handles_connection_error(hass):
    hub = SatelHub("host", 1234, "code")
    hub.send_command = AsyncMock(side_effect=ConnectionError)
    coordinator = DataUpdateCoordinator(
        hass,
        logging.getLogger(__name__),
        name="satel",
        update_method=AsyncMock(return_value={}),
        config_entry=MockConfigEntry(domain="satel"),
    )
    entity = SatelOutputSwitch(hub, coordinator, "1", "Out")
    entity.async_write_ha_state = MagicMock()
    entity.coordinator.async_request_refresh = AsyncMock()
    coordinator.data = {"outputs": {"1": "OFF"}}

    await entity.async_turn_on()

    assert not entity.is_on
    entity.async_write_ha_state.assert_not_called()
    entity.coordinator.async_request_refresh.assert_not_called()


@pytest.mark.asyncio
async def test_switch_turn_off_handles_connection_error(hass):
    hub = SatelHub("host", 1234, "code")
    hub.send_command = AsyncMock(side_effect=ConnectionError)
    coordinator = DataUpdateCoordinator(
        hass,
        logging.getLogger(__name__),
        name="satel",
        update_method=AsyncMock(return_value={"outputs": {"1": "ON"}}),
        config_entry=MockConfigEntry(domain="satel"),
    )
    entity = SatelOutputSwitch(hub, coordinator, "1", "Out")
    entity._attr_is_on = True
    entity.async_write_ha_state = MagicMock()
    entity.coordinator.async_request_refresh = AsyncMock()
    coordinator.data = {"outputs": {"1": "ON"}}

    await entity.async_turn_off()

    assert entity.is_on
    entity.async_write_ha_state.assert_not_called()
    entity.coordinator.async_request_refresh.assert_not_called()
