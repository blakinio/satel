import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.satel import SatelHub, async_unload_entry, PLATFORMS
from custom_components.satel.const import DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry


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
async def test_async_close():
    hub = SatelHub("1.2.3.4", 1234)
    writer = MagicMock()
    writer.close = MagicMock()
    writer.wait_closed = AsyncMock()
    hub._writer = writer

    await hub.async_close()

    writer.close.assert_called_once()
    writer.wait_closed.assert_awaited_once()
    assert hub._writer is None


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
