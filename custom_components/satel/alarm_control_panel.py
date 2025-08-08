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

from . import SatelHub, SatelRuntimeData
from .entity import SatelEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up Satel alarm control panel from a config entry."""
    data: SatelRuntimeData = entry.runtime_data
    hub: SatelHub = data.hub
    coordinator = data.coordinator
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
    _attr_translation_key = "partition"

    def __init__(self, hub: SatelHub, coordinator, partition: str) -> None:
        super().__init__(hub, coordinator)
        self._partition = partition
        self._attr_unique_id = f"satel_alarm_{partition}"
        self._attr_state = STATE_ALARM_DISARMED
        self._attr_translation_placeholders = {"partition": partition}

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
        if alarm == "ARMED_AWAY":
            return STATE_ALARM_ARMED_AWAY
        if alarm == "ARMED_HOME":
            return STATE_ALARM_ARMED_HOME
        if alarm == "ARMED_NIGHT":
            return STATE_ALARM_ARMED_NIGHT
        if alarm == "PENDING":
            return STATE_ALARM_PENDING
        if alarm == "TRIGGERED":
            return STATE_ALARM_TRIGGERED
        return STATE_ALARM_DISARMED

