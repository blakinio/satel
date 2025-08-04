from unittest.mock import MagicMock

from custom_components.satel.sensor import SatelZoneSensor


def test_zone_sensor_native_value_precedence():
    hub = MagicMock()
    coordinator = MagicMock()
    coordinator.data = {
        "zones": {"1": "ON"},
        "tamper": {"1": "OFF"},
        "troubles": {"1": "OFF"},
        "bypass": {"1": "OFF"},
        "alarm_memory": {"1": "OFF"},
    }
    sensor = SatelZoneSensor(hub, coordinator, "1", "Zone")

    assert sensor.native_value == "on"

    coordinator.data["tamper"]["1"] = "ON"
    assert sensor.native_value == "tamper"

    coordinator.data["tamper"]["1"] = "OFF"
    coordinator.data["troubles"]["1"] = "ON"
    assert sensor.native_value == "trouble"

    coordinator.data["troubles"]["1"] = "OFF"
    coordinator.data["bypass"]["1"] = "ON"
    assert sensor.native_value == "bypass"

    coordinator.data["bypass"]["1"] = "OFF"
    coordinator.data["alarm_memory"]["1"] = "ON"
    assert sensor.native_value == "alarm_memory"
