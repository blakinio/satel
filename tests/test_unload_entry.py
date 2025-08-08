import pytest
from unittest.mock import AsyncMock

from custom_components.satel import SatelHub, SatelRuntimeData, async_unload_entry
from custom_components.satel.const import DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.mark.asyncio
async def test_unload_entry_closes_connection_and_removes_entry(hass):
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    hub = SatelHub("host", 1234, "code")
    hub.async_close = AsyncMock()

    entry.runtime_data = SatelRuntimeData(hub, {}, None)

    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    result = await async_unload_entry(hass, entry)

    assert result
    hub.async_close.assert_awaited_once()
    assert entry.runtime_data is None
