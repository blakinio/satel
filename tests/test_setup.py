from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.satel.const import DOMAIN, DEFAULT_HOST, DEFAULT_PORT


@pytest.mark.asyncio
async def test_setup_creates_entities(hass, enable_custom_integrations):
    """Test setting up the Satel integration creates entities."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_HOST: DEFAULT_HOST, CONF_PORT: DEFAULT_PORT})
    entry.add_to_hass(hass)

    with patch("custom_components.satel.SatelHub.connect", AsyncMock()), \
        patch("custom_components.satel.SatelHub.get_status", AsyncMock(return_value={"raw": "ALARM"})):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.satel_alarm")
    assert state is not None
    assert state.state == "on"

    state = hass.states.get("sensor.satel_status")
    assert state is not None
    assert state.state == "ALARM"


@pytest.mark.asyncio
async def test_switch_services(hass, enable_custom_integrations):
    """Ensure switch entity calls hub on service invocations."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_HOST: DEFAULT_HOST, CONF_PORT: DEFAULT_PORT})
    entry.add_to_hass(hass)

    with patch("custom_components.satel.SatelHub.connect", AsyncMock()), \
        patch(
            "custom_components.satel.SatelHub.get_status",
            AsyncMock(return_value={"raw": "READY"}),
        ), \
        patch(
            "custom_components.satel.SatelHub.send_command", AsyncMock()
        ) as mock_send:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        entity_id = "switch.satel_output"

        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": entity_id}, blocking=True
        )
        assert mock_send.await_args_list[0].args[0] == "OUTPUT ON"
        assert hass.states.get(entity_id).state == "on"

        await hass.services.async_call(
            "switch", "turn_off", {"entity_id": entity_id}, blocking=True
        )
        assert mock_send.await_args_list[1].args[0] == "OUTPUT OFF"
        assert hass.states.get(entity_id).state == "off"
