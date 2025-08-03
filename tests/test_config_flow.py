from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import data_entry_flow
from homeassistant.const import CONF_HOST, CONF_PORT

from custom_components.satel.const import (
    DOMAIN,
    CONF_CODE,
    CONF_ENCODING,
    DEFAULT_ENCODING,
)


@pytest.mark.asyncio
async def test_config_flow_full(hass, enable_custom_integrations):
    devices = {
        "zones": [{"id": "1", "name": "Zone"}],
        "outputs": [{"id": "2", "name": "Out"}],
    }
    with patch("custom_components.satel.config_flow.SatelHub") as hub_cls:
        hub = hub_cls.return_value
        hub.connect = AsyncMock()
        hub.discover_devices = AsyncMock(return_value=devices)

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
                CONF_ENCODING: DEFAULT_ENCODING,
            },
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "select"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"zones": ["1"], "outputs": ["2"]}
        )

        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["title"] == "Satel 1.2.3.4"
        assert result["data"] == {
            CONF_HOST: "1.2.3.4",
            CONF_PORT: 1234,
            CONF_CODE: "abcd",
            CONF_ENCODING: DEFAULT_ENCODING,
            "zones": ["1"],
            "outputs": ["2"],
        }

        hub.connect.assert_awaited_once()
        hub.discover_devices.assert_awaited_once()


@pytest.mark.asyncio
async def test_config_flow_cannot_connect(hass, enable_custom_integrations):
    with patch("custom_components.satel.config_flow.SatelHub") as hub_cls:
        hub = hub_cls.return_value
        hub.connect = AsyncMock(side_effect=ConnectionError)

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "1.2.3.4", CONF_PORT: 1234, CONF_CODE: "abcd"}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {"base": "cannot_connect"}

        hub.connect.assert_awaited_once()
        hub.discover_devices.assert_not_called()
