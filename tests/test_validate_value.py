from airthings_ble.const import CO2_MAX, PERCENTAGE_MAX, RADON_MAX
from airthings_ble.parser import validate_value, illuminance_converter


def test_validate_value_humidity():
    valid_humidity_values = [0, 50, 100.0]
    for value in valid_humidity_values:
        assert validate_value(value=value, max_value=PERCENTAGE_MAX) == value

    invalid_humidity_values = [-1, 100.1, 101]
    for value in invalid_humidity_values:
        assert validate_value(value=value, max_value=PERCENTAGE_MAX) is None


def test_validate_value_radon():
    valid_radon_values = [0, 100, 1000.0, 16383]
    for value in valid_radon_values:
        assert validate_value(value=value, max_value=RADON_MAX) == value

    invalid_radon_values = [-1, 16384, 65535]
    for value in invalid_radon_values:
        assert validate_value(value=value, max_value=RADON_MAX) is None


def test_validate_value_co2():
    valid_co2_values = [0, 100, 1000.0, 65534]
    for value in valid_co2_values:
        assert validate_value(value=value, max_value=CO2_MAX) == value

    invalid_co2_values = [-1, 65535]
    for value in invalid_co2_values:
        assert validate_value(value=value, max_value=CO2_MAX) is None


def test_validate_value_illuminance():
    assert illuminance_converter(0) == 0
    assert illuminance_converter(255) == 100
