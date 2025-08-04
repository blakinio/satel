"""Core helpers for Home Assistant stubs used in tests."""

from __future__ import annotations

from typing import Any, Dict


class ConfigEntries:
    """Provide minimal config entries API."""
    def __init__(self) -> None:
        self._entries: dict[str, Any] = {}

    async def async_setup(self, entry_id: str) -> bool:
        return True

    async def async_forward_entry_setups(self, entry: Any, platforms: list[str]) -> bool:
        return True

    async def async_unload_platforms(self, entry: Any, platforms: list[str]) -> bool:
        return True

    async def async_unload(self, entry_id: str) -> bool:
        self._entries.pop(entry_id, None)
        return True


class HomeAssistant:
    """Simplified HomeAssistant object for tests."""

    def __init__(self) -> None:
        self.data: Dict[str, Any] = {}
        self.config_entries = ConfigEntries()

