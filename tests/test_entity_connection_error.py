from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.satel import SatelHub
from custom_components.satel.binary_sensor import SatelZoneBinarySensor
from custom_components.satel.sensor import SatelZoneSensor
from custom_components.satel.switch import SatelOutputSwitch


@pytest.mark.asyncio
async def test_binary_sensor_update_handles_connection_error():
    hub = SatelHub("host", 1234, "code")
    hub.send_command = AsyncMock(side_effect=ConnectionError)
    entity = SatelZoneBinarySensor(hub, "1", "Zone")
    entity._attr_is_on = True

    await entity.async_update()

    assert entity.is_on is None


@pytest.mark.asyncio
async def test_sensor_update_handles_connection_error():
    hub = SatelHub("host", 1234, "code")
    hub.send_command = AsyncMock(side_effect=ConnectionError)
    entity = SatelZoneSensor(hub, "1", "Zone")
    entity._attr_native_value = "value"

    await entity.async_update()

    assert entity.native_value is None


@pytest.mark.asyncio
async def test_switch_update_handles_connection_error():
    hub = SatelHub("host", 1234, "code")
    hub.send_command = AsyncMock(side_effect=ConnectionError)
    entity = SatelOutputSwitch(hub, "1", "Out")
    entity._attr_is_on = True

    await entity.async_update()

    assert entity.is_on is None


@pytest.mark.asyncio
async def test_switch_turn_on_handles_connection_error():
    hub = SatelHub("host", 1234, "code")
    hub.send_command = AsyncMock(side_effect=ConnectionError)
    entity = SatelOutputSwitch(hub, "1", "Out")
    entity.async_write_ha_state = MagicMock()

    await entity.async_turn_on()

    assert entity.is_on is False
    entity.async_write_ha_state.assert_not_called()


@pytest.mark.asyncio
async def test_switch_turn_off_handles_connection_error():
    hub = SatelHub("host", 1234, "code")
    hub.send_command = AsyncMock(side_effect=ConnectionError)
    entity = SatelOutputSwitch(hub, "1", "Out")
    entity._attr_is_on = True
    entity.async_write_ha_state = MagicMock()

    await entity.async_turn_off()

    assert entity.is_on is True
    entity.async_write_ha_state.assert_not_called()
