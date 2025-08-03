from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.satel import SatelHub


@pytest.mark.asyncio
async def test_send_command_reconnect_success(monkeypatch):
    hub = SatelHub("host", 1234, "code")

    reader1 = AsyncMock()
    writer1 = MagicMock()
    writer1.write = MagicMock(side_effect=ConnectionResetError)
    writer1.drain = AsyncMock()
    hub._reader = reader1
    hub._writer = writer1

    reader2 = AsyncMock()
    reader2.readline = AsyncMock(return_value=b"OK\n")
    writer2 = MagicMock()
    writer2.write = MagicMock()
    writer2.drain = AsyncMock()

    async def reconnect():
        hub._reader = reader2
        hub._writer = writer2

    reconnect_mock = AsyncMock(side_effect=reconnect)
    monkeypatch.setattr(hub, "_reconnect", reconnect_mock)

    response = await hub.send_command("TEST")

    reconnect_mock.assert_awaited_once()
    writer2.write.assert_called_once_with(b"TEST\n")
    assert response == "OK"


@pytest.mark.asyncio
async def test_send_command_reconnect_failure(monkeypatch):
    hub = SatelHub("host", 1234, "code")

    reader = AsyncMock()
    writer = MagicMock()
    writer.write = MagicMock(side_effect=BrokenPipeError)
    writer.drain = AsyncMock()
    hub._reader = reader
    hub._writer = writer

    reconnect_mock = AsyncMock(side_effect=ConnectionError)
    monkeypatch.setattr(hub, "_reconnect", reconnect_mock)

    with pytest.raises(ConnectionError):
        await hub.send_command("CMD")

    reconnect_mock.assert_awaited_once()
