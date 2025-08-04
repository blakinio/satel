from unittest.mock import AsyncMock, MagicMock

import pytest

import logging

from custom_components.satel import SatelHub
from custom_components.satel.const import DOMAIN
from custom_components.satel import binary_sensor, sensor, switch
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.mark.asyncio
async def test_binary_sensor_setup_entry(hass, enable_custom_integrations):
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    hub = SatelHub("host", 1234, "code")
    satel = AsyncMock()
    satel.get_zone_names = AsyncMock(return_value={1: "Zone"})
    satel.get_output_names = AsyncMock(return_value={})
    satel._monitored_zones = []
    satel._monitored_outputs = []
    hub._satel = satel
    devices = await hub.discover_devices()

    async def _update():
        return {
            "alarm": {},
            "zones": {},
            "outputs": {},
            "troubles": {},
            "tamper": {},
            "bypass": {},
            "alarm_memory": {},
        }

    coordinator = DataUpdateCoordinator(
        hass,
        logging.getLogger(__name__),
        name="satel",
        update_method=_update,
        config_entry=MockConfigEntry(domain=DOMAIN),
    )
    hass.data[DOMAIN] = {
        entry.entry_id: {"hub": hub, "devices": devices, "coordinator": coordinator}
    }

    add_entities = MagicMock()
    await binary_sensor.async_setup_entry(hass, entry, add_entities)

    add_entities.assert_called_once()
    entities = add_entities.call_args[0][0]
    assert len(entities) == 1
    assert entities[0].unique_id == "satel_zone_1"


@pytest.mark.asyncio
async def test_sensor_setup_entry(hass, enable_custom_integrations):
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    hub = SatelHub("host", 1234, "code")
    satel = AsyncMock()
    satel.get_zone_names = AsyncMock(return_value={1: "Zone"})
    satel.get_output_names = AsyncMock(return_value={})
    satel._monitored_zones = []
    satel._monitored_outputs = []
    hub._satel = satel
    devices = await hub.discover_devices()

    async def _update2():
        return {
            "alarm": {},
            "zones": {},
            "outputs": {},
            "troubles": {},
            "tamper": {},
            "bypass": {},
            "alarm_memory": {},
        }

    coordinator = DataUpdateCoordinator(
        hass,
        logging.getLogger(__name__),
        name="satel",
        update_method=_update2,
        config_entry=MockConfigEntry(domain=DOMAIN),
    )
    hass.data[DOMAIN] = {
        entry.entry_id: {"hub": hub, "devices": devices, "coordinator": coordinator}
    }

    add_entities = MagicMock()
    await sensor.async_setup_entry(hass, entry, add_entities)

    add_entities.assert_called_once()
    entities = add_entities.call_args[0][0]
    assert len(entities) == 1
    assert entities[0].unique_id == "satel_zone_status_1"


@pytest.mark.asyncio
async def test_switch_setup_entry(hass, enable_custom_integrations):
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    hub = SatelHub("host", 1234, "code")
    satel = AsyncMock()
    satel.get_zone_names = AsyncMock(return_value={})
    satel.get_output_names = AsyncMock(return_value={1: "Out"})
    satel._monitored_zones = []
    satel._monitored_outputs = []
    hub._satel = satel
    devices = await hub.discover_devices()

    async def _update3():
        return {
            "outputs": {"1": "OFF"},
            "zones": {},
            "alarm": {},
            "troubles": {},
            "tamper": {},
            "bypass": {},
            "alarm_memory": {},
        }

    coordinator = DataUpdateCoordinator(
        hass,
        logging.getLogger(__name__),
        name="satel",
        update_method=_update3,
        config_entry=MockConfigEntry(domain=DOMAIN),
    )
    hass.data[DOMAIN] = {
        entry.entry_id: {"hub": hub, "devices": devices, "coordinator": coordinator}
    }

    add_entities = MagicMock()
    await switch.async_setup_entry(hass, entry, add_entities)

    add_entities.assert_called_once()
    entities = add_entities.call_args[0][0]
    assert len(entities) == 1
    assert entities[0].unique_id == "satel_output_1"
