"""Satel alarm control panel."""

from __future__ import annotations

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
)
from homeassistant.core import HomeAssistant

from . import SatelHub
from .const import DOMAIN
from .entity import SatelEntity

ALARM_STATE_MAP = {
    "ARMED_AWAY": STATE_ALARM_ARMED_AWAY,
    "ARMED_HOME": STATE_ALARM_ARMED_HOME,
    "ARMED_NIGHT": STATE_ALARM_ARMED_NIGHT,
    "PENDING": STATE_ALARM_PENDING,
    "TRIGGERED": STATE_ALARM_TRIGGERED,
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up Satel alarm control panel from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    hub: SatelHub = data["hub"]
    coordinator = data["coordinator"]
    partitions = entry.data.get("partitions") or ["1"]
    async_add_entities(
        [SatelAlarmPanel(hub, coordinator, part) for part in partitions]
    )


class SatelAlarmPanel(SatelEntity, AlarmControlPanelEntity):
    """Representation of a Satel partition."""

    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_AWAY
        | AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_NIGHT
    )

    def __init__(self, hub: SatelHub, coordinator, partition: str) -> None:
        super().__init__(hub, coordinator)
        self._partition = partition
        self._attr_name = f"Satel Alarm {partition}"
        self._attr_unique_id = f"satel_alarm_{partition}"
        self._attr_state = STATE_ALARM_DISARMED

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        await self._hub.arm(self._partition)
        await self.coordinator.async_request_refresh()

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        await self._hub.arm_home(self._partition)
        await self.coordinator.async_request_refresh()

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        await self._hub.arm_night(self._partition)
        await self.coordinator.async_request_refresh()

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        await self._hub.disarm_partition(self._partition)
        await self.coordinator.async_request_refresh()

    @property
    def state(self) -> str:
        alarm = (
            self.coordinator.data.get("alarm", {}).get(str(self._partition), "")
        ).upper()
        return ALARM_STATE_MAP.get(alarm, STATE_ALARM_DISARMED)

