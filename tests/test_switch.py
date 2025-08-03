from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.satel import SatelHub
from custom_components.satel.switch import SatelOutputSwitch


@pytest.mark.asyncio
async def test_turn_on_writes_state():
    hub = SatelHub("host", 1234, "code")
    hub.send_command = AsyncMock()
    switch = SatelOutputSwitch(hub, "1", "Out")
    switch.async_write_ha_state = MagicMock()

    await switch.async_turn_on()

    assert switch.is_on
    switch.async_write_ha_state.assert_called_once()


@pytest.mark.asyncio
async def test_turn_off_writes_state():
    hub = SatelHub("host", 1234, "code")
    hub.send_command = AsyncMock()
    switch = SatelOutputSwitch(hub, "1", "Out")
    switch._attr_is_on = True
    switch.async_write_ha_state = MagicMock()

    await switch.async_turn_off()

    assert not switch.is_on
    switch.async_write_ha_state.assert_called_once()
