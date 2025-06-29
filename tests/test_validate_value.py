from airthings_ble.const import CO2_MAX, PERCENTAGE_MAX, PRESSURE_MAX, RADON_MAX
from airthings_ble.parser import illuminance_converter, validate_value


def test_validate_value_humidity() -> None:
    valid_humidity_values = [0, 50, 100.0]
    for value in valid_humidity_values:
        assert validate_value(value=value, max_value=PERCENTAGE_MAX) == value

    invalid_humidity_values = [-1, 100.1, 101]
    for value in invalid_humidity_values:
        assert validate_value(value=value, max_value=PERCENTAGE_MAX) is None


def test_validate_value_radon() -> None:
    valid_radon_values = [0, 100, 1000.0, 16383]
    for value in valid_radon_values:
        assert validate_value(value=value, max_value=RADON_MAX) == value

    invalid_radon_values = [-1, 16384, 65535]
    for value in invalid_radon_values:
        assert validate_value(value=value, max_value=RADON_MAX) is None


def test_validate_value_co2() -> None:
    valid_co2_values = [0, 100, 1000.0, 65534]
    for value in valid_co2_values:
        assert validate_value(value=value, max_value=CO2_MAX) == value

    invalid_co2_values = [-1, 65535]
    for value in invalid_co2_values:
        assert validate_value(value=value, max_value=CO2_MAX) is None


def test_validate_value_illuminance() -> None:
    assert illuminance_converter(0) == 0
    assert illuminance_converter(255) == 100
    assert illuminance_converter(256) is None


def test_validata_value_pressure() -> None:
    assert validate_value(value=0.0, max_value=PRESSURE_MAX) == 0
    assert validate_value(value=1310.0, max_value=PRESSURE_MAX) == 1310
    assert validate_value(value=1311.0, max_value=PRESSURE_MAX) is None
    assert validate_value(value=-1.0, max_value=PRESSURE_MAX) is None
    assert validate_value(value=65535.0, max_value=PRESSURE_MAX) is None
