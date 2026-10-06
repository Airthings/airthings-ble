import logging

import pytest
from airthings_ble.command_decode import WaveRadonAndPlusCommandDecode
from airthings_ble.const import (
    BATTERY,
    CHAR_UUID_WAVE_PLUS_DATA,
    CO2,
    HUMIDITY,
    ILLUMINANCE,
    PRESSURE,
    RADON_1DAY_AVG,
    RADON_LONGTERM_AVG,
    TEMPERATURE,
    VOC,
)
from airthings_ble.sensor_decoders import SENSOR_DECODERS, _decode_wave_plus

_LOGGER = logging.getLogger(__name__)


def test_wave_plus_command_decode() -> None:
    """Test wave plus command decode."""
    decode = WaveRadonAndPlusCommandDecode()
    assert decode.decode_data(
        logger=_LOGGER,
        raw_data=bytearray.fromhex(
            "6d00600c04000100008211ff00000000c04c20001f3560007006B80B0900"
        ),
    ) == {BATTERY: 3.0}


def test_wave_plus_sensor_data() -> None:
    """Test wave plus sensor data."""
    raw_data = bytearray.fromhex("01380d800b002200bd094cc31d036c0000007d05")

    decoded_data = _decode_wave_plus(name="Plus", format_type="<4B8H", scale=1.0)(
        raw_data
    )

    assert decoded_data[HUMIDITY] == 28.0
    assert decoded_data[RADON_1DAY_AVG] == 11
    assert decoded_data[RADON_LONGTERM_AVG] == 34
    assert decoded_data[TEMPERATURE] == 24.93
    assert decoded_data[VOC] == 108
    assert decoded_data[CO2] == 797
    assert decoded_data[ILLUMINANCE] == 5
    assert decoded_data[PRESSURE] == 999.92


def test_wave_plus_sensor_data_below_zero() -> None:
    """Test wave plus temperature below zero."""
    decoded_data = SENSOR_DECODERS[str(CHAR_UUID_WAVE_PLUS_DATA)](
        bytearray.fromhex("01380d800b0022000cfe4cc31d036c0000007d05")
    )

    assert decoded_data[TEMPERATURE] == -5.0
    assert decoded_data[HUMIDITY] == 28.0
    assert decoded_data[RADON_1DAY_AVG] == 11
    assert decoded_data[RADON_LONGTERM_AVG] == 34
    assert decoded_data[PRESSURE] == 999.92
    assert decoded_data[CO2] == 797
    assert decoded_data[VOC] == 108


@pytest.mark.parametrize(
    ("raw_temperature", "temperature"),
    [
        pytest.param("60f0", -40.0, id="min"),
        pytest.param("5ff0", None, id="below_min"),
        pytest.param("1027", 100.0, id="max"),
        pytest.param("1127", None, id="above_max"),
    ],
)
def test_wave_plus_temperature_bounds(
    raw_temperature: str, temperature: float | None
) -> None:
    """Test wave plus temperatures are kept only between -40 and 100 °C."""
    decoded_data = SENSOR_DECODERS[str(CHAR_UUID_WAVE_PLUS_DATA)](
        bytearray.fromhex(f"01380d800b002200{raw_temperature}4cc31d036c0000007d05")
    )

    assert decoded_data[TEMPERATURE] == temperature


def test_wave_plus_sensor_data_without_humidity_has_no_temperature() -> None:
    """Test the firmware's invalid reading without humidity gives no temperature."""
    decoded_data = SENSOR_DECODERS[str(CHAR_UUID_WAVE_PLUS_DATA)](
        bytearray.fromhex("01ff3a0025000000ffffffff5a02ffff0000ffff")
    )

    assert decoded_data[HUMIDITY] is None
    assert decoded_data[TEMPERATURE] is None


def test_wave_plus_sensor_data_without_temperature() -> None:
    """Test a temperature of 0xFFFF gives no temperature."""
    decoded_data = SENSOR_DECODERS[str(CHAR_UUID_WAVE_PLUS_DATA)](
        bytearray.fromhex("01380d800b002200ffff4cc31d036c0000007d05")
    )

    assert decoded_data[HUMIDITY] == 28.0
    assert decoded_data[TEMPERATURE] is None


def test_wave_plus_sensor_data_with_invalid_humidity_has_no_temperature() -> None:
    """Test a valid temperature is dropped when the humidity is invalid."""
    decoded_data = SENSOR_DECODERS[str(CHAR_UUID_WAVE_PLUS_DATA)](
        bytearray.fromhex("01ff0d800b002200bd094cc31d036c0000007d05")
    )

    assert decoded_data[HUMIDITY] is None
    assert decoded_data[TEMPERATURE] is None
