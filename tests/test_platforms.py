from unittest.mock import MagicMock

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
    devices = {"zones": [{"id": "1", "name": "Zone"}], "outputs": []}
    async def _update():
        return {}

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
    devices = {"zones": [{"id": "1", "name": "Zone"}], "outputs": []}
    async def _update2():
        return {}

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
    devices = {"zones": [], "outputs": [{"id": "1", "name": "Out"}]}
    async def _update3():
        return {"outputs": {"1": "OFF"}, "zones": {}, "alarm": {}}

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
