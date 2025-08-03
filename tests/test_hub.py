import asyncio
import sys
from types import ModuleType
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

# Minimal stubs for the Home Assistant modules used by SatelHub
homeassistant = ModuleType("homeassistant")
config_entries = ModuleType("homeassistant.config_entries")


class ConfigEntry:  # type: ignore
    pass


config_entries.ConfigEntry = ConfigEntry
const = ModuleType("homeassistant.const")
const.CONF_HOST = "host"
const.CONF_PORT = "port"
core = ModuleType("homeassistant.core")


class HomeAssistant:  # type: ignore
    pass


core.HomeAssistant = HomeAssistant
helpers = ModuleType("homeassistant.helpers")
typing_mod = ModuleType("homeassistant.helpers.typing")
typing_mod.ConfigType = dict[str, Any]
helpers.typing = typing_mod

homeassistant.config_entries = config_entries
homeassistant.const = const
homeassistant.core = core
homeassistant.helpers = helpers

sys.modules.setdefault("homeassistant", homeassistant)
sys.modules.setdefault("homeassistant.config_entries", config_entries)
sys.modules.setdefault("homeassistant.const", const)
sys.modules.setdefault("homeassistant.core", core)
sys.modules.setdefault("homeassistant.helpers", helpers)
sys.modules.setdefault("homeassistant.helpers.typing", typing_mod)

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
    assert not hub._lock.locked()


@pytest.mark.asyncio
async def test_parallel_commands_serialized():
    hub = SatelHub("1.2.3.4", 1234, "abcd")
    reader = AsyncMock()
    writer = MagicMock()
    writer.drain = AsyncMock()
    writer.write = MagicMock()
    hub._reader = reader
    hub._writer = writer

    finish_first = asyncio.Event()
    call_count = 0

    async def readline_side_effect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            await finish_first.wait()
            return b"OK1\n"
        return b"OK2\n"

    reader.readline.side_effect = readline_side_effect

    task1 = asyncio.create_task(hub.send_command("CMD1"))
    await asyncio.sleep(0)
    assert writer.write.call_count == 1

    task2 = asyncio.create_task(hub.send_command("CMD2"))
    await asyncio.sleep(0)
    assert writer.write.call_count == 1

    finish_first.set()
    responses = await asyncio.gather(task1, task2)

    assert responses == ["OK1", "OK2"]
    assert writer.write.call_count == 2
    assert not hub._lock.locked()


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
