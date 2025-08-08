from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.satel.const import (
    DOMAIN,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_ENCODING,
    CONF_UPDATE_INTERVAL,
    CONF_TIMEOUT,
    CONF_RECONNECT_DELAY,
    CONF_ENCRYPTION_METHOD,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_TIMEOUT,
    DEFAULT_RECONNECT_DELAY,
    DEFAULT_ENCRYPTION_METHOD,
)


@pytest.mark.asyncio
async def test_setup_creates_entities(hass, enable_custom_integrations):
    """Test setting up the Satel integration creates entities."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_HOST: DEFAULT_HOST, CONF_PORT: DEFAULT_PORT})
    entry.add_to_hass(hass)

    with patch("custom_components.satel.SatelHub.connect", AsyncMock()), \
        patch(
            "custom_components.satel.SatelHub.start_monitoring",
            AsyncMock(return_value=Mock()),
        ), \
        patch(
            "custom_components.satel.SatelHub.discover_devices",
            AsyncMock(return_value={"zones": [], "outputs": []}),
        ), \
        patch(
            "custom_components.satel.SatelHub.get_overview",
            AsyncMock(
                return_value={
                    "alarm": {"1": "TRIGGERED"},
                    "zones": {},
                    "outputs": {},
                    "troubles": {},
                    "tamper": {},
                    "bypass": {},
                    "alarm_memory": {},
                }
            ),
        ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.satel_alarm")
    assert state is not None
    assert state.state == "on"

    state = hass.states.get("sensor.satel_status")
    assert state is not None
    assert state.state == "TRIGGERED"


@pytest.mark.asyncio
async def test_switch_services(hass, enable_custom_integrations):
    """Ensure switch entity calls hub on service invocations."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_HOST: DEFAULT_HOST, CONF_PORT: DEFAULT_PORT})
    entry.add_to_hass(hass)

    with patch("custom_components.satel.SatelHub.connect", AsyncMock()), \
        patch(
            "custom_components.satel.SatelHub.start_monitoring",
            AsyncMock(return_value=Mock()),
        ), \
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
                    {
                        "alarm": {"1": "READY"},
                        "zones": {},
                        "outputs": {"1": "OFF"},
                        "troubles": {},
                        "tamper": {},
                        "bypass": {},
                        "alarm_memory": {},
                    },
                    {
                        "alarm": {"1": "READY"},
                        "zones": {},
                        "outputs": {"1": "ON"},
                        "troubles": {},
                        "tamper": {},
                        "bypass": {},
                        "alarm_memory": {},
                    },
                    {
                        "alarm": {"1": "READY"},
                        "zones": {},
                        "outputs": {"1": "ON"},
                        "troubles": {},
                        "tamper": {},
                        "bypass": {},
                        "alarm_memory": {},
                    },
                    {
                        "alarm": {"1": "READY"},
                        "zones": {},
                        "outputs": {"1": "OFF"},
                        "troubles": {},
                        "tamper": {},
                        "bypass": {},
                        "alarm_memory": {},
                    },
                    {
                        "alarm": {"1": "READY"},
                        "zones": {},
                        "outputs": {"1": "OFF"},
                        "troubles": {},
                        "tamper": {},
                        "bypass": {},
                        "alarm_memory": {},
                    },
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


@pytest.mark.asyncio
async def test_setup_uses_options(hass, enable_custom_integrations):
    """Ensure options override data when setting up the hub."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: DEFAULT_HOST,
            CONF_PORT: DEFAULT_PORT,
            CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
            CONF_TIMEOUT: DEFAULT_TIMEOUT,
            CONF_RECONNECT_DELAY: DEFAULT_RECONNECT_DELAY,
            CONF_ENCRYPTION_METHOD: DEFAULT_ENCRYPTION_METHOD,
        },
        options={
            CONF_UPDATE_INTERVAL: 1,
            CONF_TIMEOUT: 2,
            CONF_RECONNECT_DELAY: 3,
            CONF_ENCRYPTION_METHOD: DEFAULT_ENCRYPTION_METHOD,
        },
    )
    entry.add_to_hass(hass)

    with patch("custom_components.satel.SatelHub") as hub_cls:
        hub = hub_cls.return_value
        hub.connect = AsyncMock()
        hub.start_monitoring = AsyncMock(return_value=Mock())
        hub.discover_devices = AsyncMock(return_value={"zones": [], "outputs": []})
        hub.get_overview = AsyncMock(
            return_value={
                "alarm": {},
                "zones": {},
                "outputs": {},
                "troubles": {},
                "tamper": {},
                "bypass": {},
                "alarm_memory": {},
            }
        )
        hub.async_close = AsyncMock()
        hub.host = DEFAULT_HOST

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    hub_cls.assert_called_once_with(
        DEFAULT_HOST,
        DEFAULT_PORT,
        None,
        user_code=None,
        encryption_key=None,
        encoding=DEFAULT_ENCODING,
        update_interval=1,
        timeout=2,
        reconnect_delay=3,
        encryption_method=DEFAULT_ENCRYPTION_METHOD,
    )
