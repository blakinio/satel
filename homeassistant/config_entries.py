"""Configuration entry stubs used for tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ConfigEntry:
    """Simplified representation of a config entry."""

    entry_id: str = ""
    data: Dict[str, Any] | None = None

