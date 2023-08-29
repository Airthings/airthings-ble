import pytest

from airthings_ble.parser import validate_value
from airthings_ble.const import HUMIDITY_MAX as max


def test_validate_value():
    min = 0.0

    valid_humidity_values = [0, 50, 100.0]
    for value in valid_humidity_values:
        assert validate_value(value=value, min=min, max=max) == value

    invalid_humidity_values = [-1, 100.1, 101]
    for value in invalid_humidity_values:
        assert validate_value(value=value, min=min, max=max) is None
