"""Base entity for Satel integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from . import SatelHub


class SatelEntity(Entity):
    """Representation of a Satel entity."""

    def __init__(self, hub: SatelHub) -> None:
        self._hub = hub

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._hub.host)},
            manufacturer="Satel",
            name="Satel Alarm",
        )
