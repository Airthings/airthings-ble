import pytest

from airthings_ble.parser import validate_value
from airthings_ble.const import HUMIDITY_MAX, RADON_MAX

min = 0.0

def test_validate_value_humidity():
    valid_humidity_values = [0, 50, 100.0]
    for value in valid_humidity_values:
        assert validate_value(value=value, min=min, max=HUMIDITY_MAX) == value

    invalid_humidity_values = [-1, 100.1, 101]
    for value in invalid_humidity_values:
        assert validate_value(value=value, min=min, max=HUMIDITY_MAX) is None
