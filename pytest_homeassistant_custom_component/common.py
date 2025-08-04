"""Common test helpers mimicking Home Assistant utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry


@dataclass
class MockConfigEntry(ConfigEntry):
    domain: str = "test"

    def __init__(self, *, domain: str, data: Dict[str, Any] | None = None):
        super().__init__(entry_id=f"{domain}_id", data=data or {})
        self.domain = domain
        self.unique_id = domain

    def add_to_hass(self, hass) -> None:  # pragma: no cover - simple assignment
        hass.config_entries._entries[self.entry_id] = self

