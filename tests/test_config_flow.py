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


codex/handle-network-errors-in-config_flow
pytestmark = [pytest.mark.asyncio, pytest.mark.usefixtures("enable_custom_integrations")]


async def test_config_flow_full(hass):
=======
@pytest.mark.asyncio
async def test_config_flow_full(hass, enable_custom_integrations):
 main
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


 codex/handle-network-errors-in-config_flow
async def test_config_flow_cannot_connect(hass):
    """Test we handle connection errors."""
    with patch("custom_components.satel.config_flow.SatelHub") as hub_cls:
        hub = hub_cls.return_value
        hub.connect = AsyncMock(side_effect=OSError)
        hub.discover_devices = AsyncMock()
=======
@pytest.mark.asyncio
async def test_config_flow_cannot_connect(hass, enable_custom_integrations):
    with patch("custom_components.satel.config_flow.SatelHub") as hub_cls:
        hub = hub_cls.return_value
        hub.connect = AsyncMock(side_effect=ConnectionError)
 main

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
 codex/handle-network-errors-in-config_flow
            result["flow_id"], {CONF_HOST: "1.2.3.4", CONF_PORT: 1234}
        )

        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}
        hub.connect.assert_awaited_once()
        hub.discover_devices.assert_not_awaited()
=======
            result["flow_id"], {CONF_HOST: "1.2.3.4", CONF_PORT: 1234, CONF_CODE: "abcd"}
        )
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {"base": "cannot_connect"}

        hub.connect.assert_awaited_once()
        hub.discover_devices.assert_not_called()
 main
