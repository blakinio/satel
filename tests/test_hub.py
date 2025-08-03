import asyncio
import sys
import time
import types
from unittest.mock import AsyncMock, MagicMock

import pytest


homeassistant = types.ModuleType("homeassistant")
config_entries = types.ModuleType("config_entries")
class ConfigEntry:  # pragma: no cover - simple stub
    pass

config_entries.ConfigEntry = ConfigEntry
const = types.ModuleType("const")
const.CONF_HOST = "host"
const.CONF_PORT = "port"
core = types.ModuleType("core")
core.HomeAssistant = object
helpers = types.ModuleType("helpers")
helpers.typing = types.ModuleType("typing")
helpers.typing.ConfigType = dict

sys.modules.setdefault("homeassistant", homeassistant)
sys.modules.setdefault("homeassistant.config_entries", config_entries)
sys.modules.setdefault("homeassistant.const", const)
sys.modules.setdefault("homeassistant.core", core)
sys.modules.setdefault("homeassistant.helpers", helpers)
sys.modules.setdefault("homeassistant.helpers.typing", helpers.typing)

from custom_components.satel import SatelHub


@pytest.mark.asyncio
async def test_connect(monkeypatch):
    reader = AsyncMock()
    writer = AsyncMock()
    open_mock = AsyncMock(return_value=(reader, writer))
    monkeypatch.setattr(asyncio, "open_connection", open_mock)

    hub = SatelHub("1.2.3.4", 1234)
    await hub.connect()

    open_mock.assert_awaited_once_with("1.2.3.4", 1234)
    assert hub._reader is reader
    assert hub._writer is writer


@pytest.mark.asyncio
async def test_send_command(monkeypatch):
    hub = SatelHub("1.2.3.4", 1234)
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
async def test_send_command_not_connected():
    hub = SatelHub("1.2.3.4", 1234)
    with pytest.raises(ConnectionError):
        await hub.send_command("TEST")


@pytest.mark.asyncio
async def test_discover_devices(monkeypatch):
    hub = SatelHub("1.2.3.4", 1234)
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


@pytest.mark.asyncio
async def test_send_command_serialization():
    hub = SatelHub("1.2.3.4", 1234)
    reader = AsyncMock()

    async def delayed_readline():
        await asyncio.sleep(0.1)
        return b"OK\n"

    reader.readline = AsyncMock(side_effect=delayed_readline)
    writer = MagicMock()
    writer.drain = AsyncMock()
    writer.write = MagicMock()
    hub._reader = reader
    hub._writer = writer

    start = time.perf_counter()
    responses = await asyncio.gather(
        hub.send_command("CMD1"),
        hub.send_command("CMD2"),
    )
    elapsed = time.perf_counter() - start

    assert responses == ["OK", "OK"]
    assert elapsed >= 0.19
