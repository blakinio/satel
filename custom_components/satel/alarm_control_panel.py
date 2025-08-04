"""Satel alarm control panel."""

from __future__ import annotations

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ALARM_ARMED_AWAY, STATE_ALARM_DISARMED
from homeassistant.core import HomeAssistant

from . import SatelHub
from .const import DOMAIN
from .entity import SatelEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up Satel alarm control panel from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    hub: SatelHub = data["hub"]
    coordinator = data["coordinator"]
    async_add_entities([SatelAlarmPanel(hub, coordinator)])


class SatelAlarmPanel(SatelEntity, AlarmControlPanelEntity):
    """Representation of the Satel alarm panel."""

    _attr_name = "Satel Alarm"
    _attr_unique_id = "satel_alarm"
    _attr_supported_features = AlarmControlPanelEntityFeature.ARM_AWAY

    def __init__(self, hub: SatelHub, coordinator) -> None:
        super().__init__(hub, coordinator)
        self._attr_state = STATE_ALARM_DISARMED

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await self._hub.arm()
        await self.coordinator.async_request_refresh()

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        await self._hub.disarm()
        await self.coordinator.async_request_refresh()

    @property
    def state(self) -> str:
        alarm = self.coordinator.data.get("alarm", "").upper()
        if alarm == "ARMED":
            return STATE_ALARM_ARMED_AWAY
        return STATE_ALARM_DISARMED

