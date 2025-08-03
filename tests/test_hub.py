import asyncio
 codex/add-configurable-timeout-to-send_command
import logging
import sys
import types
=======
codex/wrap-asyncio.open_connection-in-try/except
import logging
=======
codex/add-asyncio.lock-to-satelhub
import sys
import time
import types
=======
 codex/implement-asyncio-lock-in-satelhub
import sys
from types import ModuleType
from typing import Any
=======
 codex/add-unit-tests-for-satelhub-integration
from unittest.mock import AsyncMock
=======
import logging
 main
 main
main
main
from unittest.mock import AsyncMock, MagicMock
 main

import pytest

codex/add-configurable-timeout-to-send_command
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
=======
 codex/refactor-async_unload_entry-to-call-async_close
from custom_components.satel import SatelHub, async_unload_entry, PLATFORMS
from custom_components.satel.const import DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry
=======
 codex/add-asyncio.lock-to-satelhub

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
=======
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
 main

sys.modules.setdefault("homeassistant", homeassistant)
sys.modules.setdefault("homeassistant.config_entries", config_entries)
sys.modules.setdefault("homeassistant.const", const)
sys.modules.setdefault("homeassistant.core", core)
sys.modules.setdefault("homeassistant.helpers", helpers)
 codex/add-asyncio.lock-to-satelhub
sys.modules.setdefault("homeassistant.helpers.typing", helpers.typing)
=======
sys.modules.setdefault("homeassistant.helpers.typing", typing_mod)
 main
main

from custom_components.satel import SatelHub
main

HOST = "1.2.3.4"
PORT = 1234
CODE = "abcd"


 codex/add-unit-tests-for-satelhub-integration
class DummyWriter:
    """Helper writer object for tests."""

    def __init__(self):
        self.data = b""

    def write(self, data: bytes) -> None:
        self.data += data

    async def drain(self) -> None:
        pass

    def close(self) -> None:  # pragma: no cover - cleanup
        pass

    async def wait_closed(self) -> None:  # pragma: no cover - cleanup
        pass


@pytest.mark.asyncio
async def test_connect_and_send_command(monkeypatch):
    """Test that commands are sent and responses are received."""
    reader = asyncio.StreamReader()
    writer = DummyWriter()

    async def mock_open_connection(host, port):
        return reader, writer

    monkeypatch.setattr(asyncio, "open_connection", mock_open_connection)

    hub = SatelHub("test", 1234)
    await hub.connect()

    reader.feed_data(b"PONG\n")
    result = await hub.send_command("PING")

    assert result == "PONG"
    assert writer.data == b"PING\n"


@pytest.mark.asyncio
async def test_get_status(monkeypatch):
    """Verify get_status wraps send_command output."""
    hub = SatelHub("host", 1234)
    monkeypatch.setattr(hub, "send_command", AsyncMock(return_value="ALARM"))

    status = await hub.get_status()

    hub.send_command.assert_awaited_once_with("STATUS")
    assert status == {"raw": "ALARM"}
=======
@pytest.mark.asyncio
async def test_connect(monkeypatch):
    reader = AsyncMock()
    writer = AsyncMock()
    open_mock = AsyncMock(return_value=(reader, writer))
    monkeypatch.setattr(asyncio, "open_connection", open_mock)
    send_mock = AsyncMock()
    monkeypatch.setattr(SatelHub, "send_command", send_mock)

    hub = SatelHub(HOST, PORT, CODE)
    await hub.connect()

    open_mock.assert_awaited_once_with(HOST, PORT)
    send_mock.assert_awaited_once_with(f"LOGIN {CODE}")
    assert hub._reader is reader
    assert hub._writer is writer


@pytest.mark.asyncio
async def test_connect_error(monkeypatch, caplog):
    open_mock = AsyncMock(side_effect=OSError("boom"))
    monkeypatch.setattr(asyncio, "open_connection", open_mock)

    hub = SatelHub("1.2.3.4", 1234)
    with caplog.at_level(logging.ERROR):
        with pytest.raises(ConnectionError):
            await hub.connect()

    open_mock.assert_awaited_once_with("1.2.3.4", 1234)
    assert "Failed to connect" in caplog.text


@pytest.mark.asyncio
async def test_send_command(monkeypatch):
    hub = SatelHub(HOST, PORT, CODE)
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
    hub = SatelHub(HOST, PORT, CODE)
    with pytest.raises(ConnectionError):
        await hub.send_command("TEST")


@pytest.mark.asyncio
 codex/wrap-send_command-in-try/except-block
async def test_send_command_reconnect(monkeypatch):
    hub = SatelHub("1.2.3.4", 1234, "abcd")

    reader1 = AsyncMock()
    writer1 = MagicMock()
    writer1.drain = AsyncMock(side_effect=ConnectionResetError)
    writer1.write = MagicMock()
    writer1.close = MagicMock()
    writer1.wait_closed = AsyncMock()
=======
async def test_send_command_reconnect_success(monkeypatch):
    hub = SatelHub(HOST, PORT, CODE)
    reader1 = AsyncMock()
    writer1 = MagicMock()
    writer1.drain = AsyncMock()
    writer1.write = MagicMock(side_effect=ConnectionResetError)
 main
    hub._reader = reader1
    hub._writer = writer1

    reader2 = AsyncMock()
    reader2.readline = AsyncMock(return_value=b"OK\n")
    writer2 = MagicMock()
    writer2.drain = AsyncMock()
    writer2.write = MagicMock()
 codex/wrap-send_command-in-try/except-block
    writer2.close = MagicMock()
    writer2.wait_closed = AsyncMock()
=======
 main

    async def reconnect():
        hub._reader = reader2
        hub._writer = writer2

 codex/wrap-send_command-in-try/except-block
    connect_mock = AsyncMock(side_effect=reconnect)
    monkeypatch.setattr(hub, "connect", connect_mock)

    response = await hub.send_command("TEST")

    writer1.write.assert_called_once_with(b"TEST\n")
    writer1.drain.assert_awaited_once()
    writer1.close.assert_called_once()
    writer1.wait_closed.assert_awaited_once()
    connect_mock.assert_awaited_once()
    writer2.write.assert_called_once_with(b"TEST\n")
    writer2.drain.assert_awaited_once()
    reader2.readline.assert_awaited_once()
=======
    monkeypatch.setattr(hub, "connect", AsyncMock(side_effect=reconnect))

    response = await hub.send_command("TEST")

    writer1.write.assert_called_once()
    hub.connect.assert_awaited_once()
    writer2.write.assert_called_once_with(b"TEST\n")
 main
    assert response == "OK"


@pytest.mark.asyncio
 codex/wrap-send_command-in-try/except-block
=======
async def test_send_command_reconnect_failure(monkeypatch):
    hub = SatelHub(HOST, PORT, CODE)
    reader1 = AsyncMock()
    writer1 = MagicMock()
    writer1.drain = AsyncMock()
    writer1.write = MagicMock(side_effect=BrokenPipeError)
    hub._reader = reader1
    hub._writer = writer1

    async def reconnect_fail():
        raise Exception("boom")

    monkeypatch.setattr(hub, "connect", AsyncMock(side_effect=reconnect_fail))

    with pytest.raises(ConnectionError):
        await hub.send_command("TEST")


@pytest.mark.asyncio
 main
async def test_discover_devices(monkeypatch):
    hub = SatelHub(HOST, PORT, CODE)
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
 codex/add-async_close-method-to-satelhub
async def test_async_close():
    hub = SatelHub("1.2.3.4", 1234)
    writer = MagicMock()
    writer.wait_closed = AsyncMock()
    hub._writer = writer
    hub._reader = AsyncMock()
=======
 codex/refactor-async_unload_entry-to-call-async_close
async def test_async_close():
    hub = SatelHub("1.2.3.4", 1234)
    writer = MagicMock()
    writer.close = MagicMock()
    writer.wait_closed = AsyncMock()
    hub._writer = writer
 main

    await hub.async_close()

    writer.close.assert_called_once()
    writer.wait_closed.assert_awaited_once()
    assert hub._writer is None
 codex/add-async_close-method-to-satelhub
    assert hub._reader is None
=======


@pytest.mark.asyncio
async def test_async_unload_entry(hass):
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    hub = SatelHub("host", 1234)
    hub.async_close = AsyncMock()
    hass.data[DOMAIN] = {entry.entry_id: {"hub": hub, "devices": {}}}
    unload = AsyncMock(return_value=True)
    hass.config_entries.async_unload_platforms = unload

    result = await async_unload_entry(hass, entry)

    assert result is True
    unload.assert_awaited_once_with(entry, PLATFORMS)
    hub.async_close.assert_awaited_once()
    assert entry.entry_id not in hass.data[DOMAIN]
=======
 codex/add-asyncio.lock-to-satelhub
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
=======
 HEAD
async def test_discover_devices_invalid_entries(monkeypatch, caplog):
    hub = SatelHub(HOST, PORT, CODE)
    monkeypatch.setattr(
        hub,
        "send_command",
        AsyncMock(return_value="1=Zone1,invalid,2=Zone2|1=Out1,broken,3=Out3"),
    )

    with caplog.at_level(logging.WARNING):
        devices = await hub.discover_devices()

    assert devices == {
        "zones": [{"id": "1", "name": "Zone1"}, {"id": "2", "name": "Zone2"}],
        "outputs": [{"id": "1", "name": "Out1"}, {"id": "3", "name": "Out3"}],
    }
    assert "Invalid zone entry" in caplog.text
    assert "Invalid output entry" in caplog.text
=======
@pytest.mark.parametrize("response", ["1=Zone1,2=Zone2", "1=Out1,3=Out3"])
async def test_discover_devices_missing_delimiter(monkeypatch, caplog, response):
    hub = SatelHub("1.2.3.4", 1234, "abcd")
    monkeypatch.setattr(hub, "send_command", AsyncMock(return_value=response))

    with caplog.at_level(logging.ERROR):
        devices = await hub.discover_devices()

    assert devices == {
        "zones": [{"id": "1", "name": "Zone 1"}],
        "outputs": [{"id": "1", "name": "Output 1"}],
    }
    assert response in caplog.text
 pr/44


@pytest.mark.asyncio
async def test_discover_devices_reconnect(monkeypatch):
    hub = SatelHub(HOST, PORT, CODE)
    connect_mock = AsyncMock()
    monkeypatch.setattr(hub, "connect", connect_mock)
    send_mock = AsyncMock(
        side_effect=[ConnectionError, "1=Zone1|1=Out1"]
    )
    monkeypatch.setattr(hub, "send_command", send_mock)

    devices = await hub.discover_devices()

    assert send_mock.await_count == 2
    connect_mock.assert_awaited_once()
    assert devices == {
        "zones": [{"id": "1", "name": "Zone1"}],
        "outputs": [{"id": "1", "name": "Out1"}],
    }


@pytest.mark.asyncio
async def test_discover_devices_reconnect_failure(monkeypatch, caplog):
    hub = SatelHub(HOST, PORT, CODE)
    connect_mock = AsyncMock()
    monkeypatch.setattr(hub, "connect", connect_mock)
    send_mock = AsyncMock(side_effect=[ConnectionError("boom"), ConnectionError("boom")])
    monkeypatch.setattr(hub, "send_command", send_mock)

    with caplog.at_level(logging.ERROR):
        devices = await hub.discover_devices()

    assert send_mock.await_count == 2
    connect_mock.assert_awaited_once()
    assert devices == {
        "zones": [{"id": "1", "name": "Zone 1"}],
        "outputs": [{"id": "1", "name": "Output 1"}],
    }
    assert "Device discovery failed after reconnection" in caplog.text
 main
 main
main
 main
