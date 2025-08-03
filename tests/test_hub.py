import asyncio
import logging
import sys
import types
from unittest.mock import AsyncMock, MagicMock

import pytest

# Provide minimal stubs for required Home Assistant modules
ha = types.ModuleType("homeassistant")
ha.config_entries = types.ModuleType("homeassistant.config_entries")
ha.config_entries.ConfigEntry = object
ha.const = types.ModuleType("homeassistant.const")
ha.const.CONF_HOST = "host"
ha.const.CONF_PORT = "port"
ha.core = types.ModuleType("homeassistant.core")
ha.core.HomeAssistant = object
ha.helpers = types.ModuleType("homeassistant.helpers")
ha.helpers.typing = types.ModuleType("homeassistant.helpers.typing")
ha.helpers.typing.ConfigType = dict

sys.modules.setdefault("homeassistant", ha)
sys.modules["homeassistant.config_entries"] = ha.config_entries
sys.modules["homeassistant.const"] = ha.const
sys.modules["homeassistant.core"] = ha.core
sys.modules["homeassistant.helpers"] = ha.helpers
sys.modules["homeassistant.helpers.typing"] = ha.helpers.typing

from custom_components.satel import SatelHub


@pytest.mark.asyncio
async def test_connect(monkeypatch):
    reader = AsyncMock()
    writer = AsyncMock()
    open_mock = AsyncMock(return_value=(reader, writer))
    monkeypatch.setattr(asyncio, "open_connection", open_mock)
    send_mock = AsyncMock()
    monkeypatch.setattr(SatelHub, "send_command", send_mock)

    hub = SatelHub("1.2.3.4", 1234, "abcd")
    await hub.connect()

    open_mock.assert_awaited_once_with("1.2.3.4", 1234)
    send_mock.assert_awaited_once_with("LOGIN abcd")
    assert hub._reader is reader
    assert hub._writer is writer


@pytest.mark.asyncio
async def test_send_command(monkeypatch):
    hub = SatelHub("1.2.3.4", 1234, "abcd")
    reader = AsyncMock()
    reader.readline = AsyncMock(return_value=b"OK\n")
    writer = MagicMock()
    writer.drain = AsyncMock()
    writer.write = MagicMock()
    hub._reader = reader
    hub._writer = writer

    response = await hub.send_command("TEST")

    writer.write.assert_called_once_with(b"TEST\n")
    writer.drain.assert_awaited_once()
    reader.readline.assert_awaited_once()
    assert response == "OK"


@pytest.mark.asyncio
async def test_send_command_timeout(caplog):
    hub = SatelHub("1.2.3.4", 1234, "abcd")
    reader = AsyncMock()

    async def slow_read():
        await asyncio.sleep(1)

    reader.readline = slow_read
    writer = MagicMock()
    writer.drain = AsyncMock()
    writer.write = MagicMock()
    hub._reader = reader
    hub._writer = writer

    with caplog.at_level(logging.ERROR), pytest.raises(asyncio.TimeoutError):
        await hub.send_command("TEST", timeout=0.01)

    assert "Timeout while sending command: TEST" in caplog.text


@pytest.mark.asyncio
async def test_send_command_not_connected():
    hub = SatelHub("1.2.3.4", 1234, "abcd")
    with pytest.raises(ConnectionError):
        await hub.send_command("TEST")


@pytest.mark.asyncio
async def test_discover_devices(monkeypatch):
    hub = SatelHub("1.2.3.4", 1234, "abcd")
    monkeypatch.setattr(
        hub,
        "send_command",
        AsyncMock(return_value="1=Zone1,2=Zone2|1=Out1,3=Out3"),
    )

    devices = await hub.discover_devices()

    assert devices == {
        "zones": [{"id": "1", "name": "Zone1"}, {"id": "2", "name": "Zone2"}],
        "outputs": [{"id": "1", "name": "Out1"}, {"id": "3", "name": "Out3"}],
    }
