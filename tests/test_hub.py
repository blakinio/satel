from unittest.mock import AsyncMock, MagicMock

import asyncio
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
async def test_connect_login_success(monkeypatch):
    hub = SatelHub("host", 1234, "code")

    open_conn_mock = AsyncMock(return_value=(AsyncMock(), AsyncMock()))
    monkeypatch.setattr(asyncio, "open_connection", open_conn_mock)

    send_command_mock = AsyncMock(return_value="OK")
    monkeypatch.setattr(hub, "send_command", send_command_mock)

    await hub.connect()

    open_conn_mock.assert_awaited_once()
    send_command_mock.assert_awaited_once_with("LOGIN code")


@pytest.mark.asyncio
async def test_connect_login_failure(monkeypatch):
    hub = SatelHub("host", 1234, "code")

    open_conn_mock = AsyncMock(return_value=(AsyncMock(), AsyncMock()))
    monkeypatch.setattr(asyncio, "open_connection", open_conn_mock)

    send_command_mock = AsyncMock(return_value="ERR")
    monkeypatch.setattr(hub, "send_command", send_command_mock)

    async def close_conn():
        hub._reader = None
        hub._writer = None

    close_mock = AsyncMock(side_effect=close_conn)
    monkeypatch.setattr(hub, "_close_connection", close_mock)

    with pytest.raises(ConnectionError):
        await hub.connect()

    send_command_mock.assert_awaited_once_with("LOGIN code")
    close_mock.assert_awaited_once()
    assert hub._reader is None
    assert hub._writer is None


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
