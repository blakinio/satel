from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import data_entry_flow
from homeassistant.const import CONF_HOST, CONF_PORT

from custom_components.satel.const import (
    DOMAIN,
    CONF_CODE,
    CONF_ENCODING,
    CONF_UPDATE_INTERVAL,
    CONF_TIMEOUT,
    CONF_RECONNECT_DELAY,
    CONF_ENCRYPTION_METHOD,
    DEFAULT_ENCODING,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_TIMEOUT,
    DEFAULT_RECONNECT_DELAY,
    DEFAULT_ENCRYPTION_METHOD,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

pytestmark = [pytest.mark.asyncio, pytest.mark.usefixtures("enable_custom_integrations")]


async def test_config_flow_full(hass):
    devices = {
        "zones": [{"id": "1", "name": "Zone"}],
        "outputs": [{"id": "2", "name": "Out"}],
        "partitions": [{"id": "1", "name": "Part1"}, {"id": "2", "name": "Part2"}],
    }
    with patch("custom_components.satel.config_flow.SatelHub") as hub_cls, \
        patch("custom_components.satel.async_setup_entry", AsyncMock(return_value=True)):
        hub = hub_cls.return_value
        hub.connect = AsyncMock()
        hub.discover_devices = AsyncMock(return_value=devices)
        hub.async_close = AsyncMock()

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.2.3.4",
                CONF_PORT: 1234,
                CONF_CODE: "abcd",
            },
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "select"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"zones": ["1"], "outputs": ["2"], "partitions": ["1", "2"]}
        )

        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["result"].unique_id == "1.2.3.4"
        assert result["title"] == "Satel 1.2.3.4"
        data = result["data"].copy()
        data.pop("user_code", None)
        data.pop("encryption_key", None)
        assert data == {
            CONF_HOST: "1.2.3.4",
            CONF_PORT: 1234,
            CONF_CODE: "abcd",
            CONF_ENCODING: DEFAULT_ENCODING,
            CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
            CONF_TIMEOUT: DEFAULT_TIMEOUT,
            CONF_RECONNECT_DELAY: DEFAULT_RECONNECT_DELAY,
            CONF_ENCRYPTION_METHOD: DEFAULT_ENCRYPTION_METHOD,
            "zones": ["1"],
            "outputs": ["2"],
            "partitions": ["1", "2"],
        }

        hub.connect.assert_awaited_once()
        hub.discover_devices.assert_awaited_once()


async def test_config_flow_cannot_connect(hass):
    with patch("custom_components.satel.config_flow.SatelHub") as hub_cls, \
        patch("custom_components.satel.async_setup_entry", AsyncMock(return_value=True)):
        hub = hub_cls.return_value
        hub.connect = AsyncMock(side_effect=ConnectionError)
        hub.discover_devices = AsyncMock()
        hub.async_close = AsyncMock()

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "1.2.3.4", CONF_PORT: 1234, CONF_CODE: "abcd"}
        )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}
        hub.connect.assert_awaited_once()
        hub.discover_devices.assert_not_called()


async def test_config_flow_already_configured(hass):
    entry = MockConfigEntry(domain=DOMAIN, unique_id="1.2.3.4")
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch("custom_components.satel.config_flow.SatelHub") as hub_cls:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "1.2.3.4", CONF_PORT: 1234, CONF_CODE: "abcd"}
        )

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    hub_cls.assert_not_called()


async def test_options_flow(hass):
    """Test configuring options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "1.2.3.4",
            CONF_PORT: 1234,
            CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
            CONF_TIMEOUT: DEFAULT_TIMEOUT,
            CONF_RECONNECT_DELAY: DEFAULT_RECONNECT_DELAY,
            CONF_ENCRYPTION_METHOD: DEFAULT_ENCRYPTION_METHOD,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_UPDATE_INTERVAL: 5,
            CONF_TIMEOUT: 6,
            CONF_RECONNECT_DELAY: 7,
            CONF_ENCRYPTION_METHOD: DEFAULT_ENCRYPTION_METHOD,
        },
    )

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert entry.options == {
        CONF_UPDATE_INTERVAL: 5,
        CONF_TIMEOUT: 6,
        CONF_RECONNECT_DELAY: 7,
        CONF_ENCRYPTION_METHOD: DEFAULT_ENCRYPTION_METHOD,
    }
