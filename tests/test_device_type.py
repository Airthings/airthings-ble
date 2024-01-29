import pytest

from airthings_ble.device_type import AirthingsDeviceType


def test_device_type():
    """Test device type."""
    assert AirthingsDeviceType.WAVE_MINI.product_name == "Wave Mini"
    assert AirthingsDeviceType.WAVE_PLUS.product_name == "Wave Plus"
    assert AirthingsDeviceType.WAVE_RADON.product_name == "Wave Radon"
    assert AirthingsDeviceType.WAVE_GEN_1.product_name == "Wave Gen 1"
    assert AirthingsDeviceType("2900") == AirthingsDeviceType.WAVE_GEN_1
    assert AirthingsDeviceType("2920") == AirthingsDeviceType.WAVE_MINI
    assert AirthingsDeviceType("2930") == AirthingsDeviceType.WAVE_PLUS
    assert AirthingsDeviceType("2950") == AirthingsDeviceType.WAVE_RADON
    with pytest.raises(ValueError):
        AirthingsDeviceType("1234")
    assert AirthingsDeviceType.from_raw_value("2900") == AirthingsDeviceType.WAVE_GEN_1
    assert AirthingsDeviceType.from_raw_value("2920") == AirthingsDeviceType.WAVE_MINI
    assert AirthingsDeviceType.from_raw_value("2930") == AirthingsDeviceType.WAVE_PLUS
    assert AirthingsDeviceType.from_raw_value("2950") == AirthingsDeviceType.WAVE_RADON
    assert AirthingsDeviceType.from_raw_value("1234") == AirthingsDeviceType.UNKNOWN


def test_battery_calculation():
    """Test battery calculation for all devices."""
    # Starting with the Wave Mini, since it has a different battery voltage range.
    # Max voltage is 4.5V, min voltage is 2.4V.

    # Starting with 5V, which is more than the max voltage
    assert AirthingsDeviceType.WAVE_MINI.battery_percentage(5.0) == 100
    assert AirthingsDeviceType.WAVE_MINI.battery_percentage(4.5) == 100
    assert AirthingsDeviceType.WAVE_MINI.battery_percentage(4.2) == 85
    assert AirthingsDeviceType.WAVE_MINI.battery_percentage(3.9) == 62
    assert AirthingsDeviceType.WAVE_MINI.battery_percentage(3.75) == 42
    assert AirthingsDeviceType.WAVE_MINI.battery_percentage(3.3) == 23
    assert AirthingsDeviceType.WAVE_MINI.battery_percentage(2.4) == 0
    assert AirthingsDeviceType.WAVE_MINI.battery_percentage(2.3) == 0

    # Repeat for the Wave Plus and Radon, which have the same battery voltage range.
    # Max voltage is 3.0V, min voltage is 2.1V.
    assert AirthingsDeviceType.WAVE_PLUS.battery_percentage(3.2) == 100
    assert AirthingsDeviceType.WAVE_PLUS.battery_percentage(3.0) == 100
    assert AirthingsDeviceType.WAVE_PLUS.battery_percentage(2.8) == 81
    assert AirthingsDeviceType.WAVE_PLUS.battery_percentage(2.6) == 53
    assert AirthingsDeviceType.WAVE_PLUS.battery_percentage(2.5) == 28
    assert AirthingsDeviceType.WAVE_PLUS.battery_percentage(2.2) == 5
    assert AirthingsDeviceType.WAVE_PLUS.battery_percentage(2.1) == 0
    assert AirthingsDeviceType.WAVE_PLUS.battery_percentage(2.0) == 0

    assert AirthingsDeviceType.WAVE_RADON.battery_percentage(3.2) == 100
    assert AirthingsDeviceType.WAVE_RADON.battery_percentage(3.0) == 100
    assert AirthingsDeviceType.WAVE_RADON.battery_percentage(2.8) == 81
    assert AirthingsDeviceType.WAVE_RADON.battery_percentage(2.6) == 53
    assert AirthingsDeviceType.WAVE_RADON.battery_percentage(2.5) == 28
    assert AirthingsDeviceType.WAVE_RADON.battery_percentage(2.2) == 5
    assert AirthingsDeviceType.WAVE_RADON.battery_percentage(2.1) == 0
    assert AirthingsDeviceType.WAVE_RADON.battery_percentage(2.0) == 0

    assert AirthingsDeviceType.WAVE_GEN_1.battery_percentage(3.2) == 100
    assert AirthingsDeviceType.WAVE_GEN_1.battery_percentage(3.0) == 100
    assert AirthingsDeviceType.WAVE_GEN_1.battery_percentage(2.8) == 81
    assert AirthingsDeviceType.WAVE_GEN_1.battery_percentage(2.6) == 53
    assert AirthingsDeviceType.WAVE_GEN_1.battery_percentage(2.5) == 28
    assert AirthingsDeviceType.WAVE_GEN_1.battery_percentage(2.2) == 5
    assert AirthingsDeviceType.WAVE_GEN_1.battery_percentage(2.1) == 0
    assert AirthingsDeviceType.WAVE_GEN_1.battery_percentage(2.0) == 0
