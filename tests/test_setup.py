from unittest.mock import AsyncMock, patch

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
        patch(
            "custom_components.satel.SatelHub.discover_devices",
            AsyncMock(return_value={"zones": [], "outputs": []}),
        ), \
        patch(
            "custom_components.satel.SatelHub.get_overview",
            AsyncMock(return_value={"alarm": "ALARM", "zones": {}, "outputs": {}}),
        ):
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
            "custom_components.satel.SatelHub.discover_devices",
            AsyncMock(
                return_value={
                    "zones": [],
                    "outputs": [{"id": "1", "name": "Satel Output"}],
                }
            ),
        ), \
        patch(
            "custom_components.satel.SatelHub.get_overview",
            AsyncMock(
                side_effect=[
                    {"alarm": "READY", "zones": {}, "outputs": {"1": "OFF"}},
                    {"alarm": "READY", "zones": {}, "outputs": {"1": "ON"}},
                    {"alarm": "READY", "zones": {}, "outputs": {"1": "ON"}},
                    {"alarm": "READY", "zones": {}, "outputs": {"1": "OFF"}},
                    {"alarm": "READY", "zones": {}, "outputs": {"1": "OFF"}},
                ]
            ),
        ), \
        patch(
            "custom_components.satel.SatelHub.set_output", AsyncMock()
        ) as mock_set:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        entity_id = "switch.satel_output"

        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": entity_id}, blocking=True
        )
        assert mock_set.await_args_list[0].args == ("1", True)

        await hass.services.async_call(
            "switch", "turn_off", {"entity_id": entity_id}, blocking=True
        )
        assert mock_set.await_args_list[1].args == ("1", False)
