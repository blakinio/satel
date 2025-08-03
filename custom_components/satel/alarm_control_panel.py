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


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up Satel alarm control panel from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    hub: SatelHub = data["hub"]
    async_add_entities([SatelAlarmPanel(hub)], True)


class SatelAlarmPanel(AlarmControlPanelEntity):
    """Representation of the Satel alarm panel."""

    _attr_name = "Satel Alarm"
    _attr_unique_id = "satel_alarm"
    _attr_supported_features = AlarmControlPanelEntityFeature.ARM_AWAY

    def __init__(self, hub: SatelHub) -> None:
        self._hub = hub
        self._attr_state = STATE_ALARM_DISARMED

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await self._hub.arm()
        self._attr_state = STATE_ALARM_ARMED_AWAY

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        await self._hub.disarm()
        self._attr_state = STATE_ALARM_DISARMED

    async def async_update(self) -> None:
        status = await self._hub.send_command("STATUS")
        if status.upper() == "ARMED":
            self._attr_state = STATE_ALARM_ARMED_AWAY
        else:
            self._attr_state = STATE_ALARM_DISARMED

