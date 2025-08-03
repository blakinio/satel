import asyncio
from unittest.mock import AsyncMock

import pytest

from custom_components.satel import SatelHub


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
