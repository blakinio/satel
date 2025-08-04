"""Minimal stub of Home Assistant DataUpdateCoordinator for tests."""

from __future__ import annotations

from typing import Any, Awaitable, Callable


class UpdateFailed(Exception):
    """Raised when an update fails."""


class DataUpdateCoordinator:
    def __init__(
        self,
        hass,
        logger,
        *,
        name: str,
        update_method: Callable[[], Awaitable[Any]],
        update_interval=None,
        config_entry=None,
    ) -> None:
        self.hass = hass
        self.logger = logger
        self.name = name
        self.update_method = update_method
        self.update_interval = update_interval
        self.config_entry = config_entry
        self.data: Any = {}
        self.last_update_success = True

    async def async_config_entry_first_refresh(self) -> None:
        await self.async_refresh()

    async def async_refresh(self) -> None:
        try:
            self.data = await self.update_method()
            self.last_update_success = True
        except Exception as err:  # pragma: no cover - simplified
            self.last_update_success = False
            raise err

    async def async_request_refresh(self) -> None:
        await self.async_refresh()

    def async_set_updated_data(self, data: Any) -> None:
        self.data = data

