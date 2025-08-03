import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

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
async def test_send_command_not_connected():
    hub = SatelHub("1.2.3.4", 1234, "abcd")
    with pytest.raises(ConnectionError):
        await hub.send_command("TEST")


@pytest.mark.asyncio
async def test_send_command_reconnect(monkeypatch):
    hub = SatelHub("1.2.3.4", 1234, "abcd")

    reader1 = AsyncMock()
    writer1 = MagicMock()
    writer1.drain = AsyncMock(side_effect=ConnectionResetError)
    writer1.write = MagicMock()
    writer1.close = MagicMock()
    writer1.wait_closed = AsyncMock()
    hub._reader = reader1
    hub._writer = writer1

    reader2 = AsyncMock()
    reader2.readline = AsyncMock(return_value=b"OK\n")
    writer2 = MagicMock()
    writer2.drain = AsyncMock()
    writer2.write = MagicMock()
    writer2.close = MagicMock()
    writer2.wait_closed = AsyncMock()

    async def reconnect():
        hub._reader = reader2
        hub._writer = writer2

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
    assert response == "OK"


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
