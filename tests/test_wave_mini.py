import logging

import pytest
from airthings_ble.command_decode import WaveMiniCommandDecode
from airthings_ble.const import (
    BATTERY,
    CHAR_UUID_WAVEMINI_DATA,
    HUMIDITY,
    ILLUMINANCE,
    PRESSURE,
    TEMPERATURE,
    VOC,
)
from airthings_ble.sensor_decoders import SENSOR_DECODERS, _decode_wave_mini

_LOGGER = logging.getLogger(__name__)


def test_wave_mini_command_decode() -> None:
    """Test Wave Mini command decode for battery."""
    decode = WaveMiniCommandDecode()
    assert decode.decode_data(
        logger=_LOGGER,
        raw_data=bytearray.fromhex(
            "6d0064000000c800000001020304f4015802bc02000020038403b80b4c04b0040000"
        ),
    ) == {BATTERY: 3.0}


def test_wave_mini_sensor_data() -> None:
    """Test Wave Mini sensor data decoding."""
    decoded_data = _decode_wave_mini(name="WaveMini", format_type="<2B5HLL", scale=1.0)(
        bytearray.fromhex("1800327431c168102e000000ff940700ffffffff")
    )

    assert decoded_data[ILLUMINANCE] == 9.0
    assert decoded_data[TEMPERATURE] == 24.31
    assert decoded_data[PRESSURE] == 989.14
    assert decoded_data[HUMIDITY] == 42.0
    assert decoded_data[VOC] == 46.0


def test_wave_mini_sensor_data_below_zero() -> None:
    """Test Wave Mini temperature below zero."""
    decoded_data = SENSOR_DECODERS[str(CHAR_UUID_WAVEMINI_DATA)](
        bytearray.fromhex("1800bf6831c168102e000000ff940700ffffffff")
    )

    assert decoded_data[TEMPERATURE] == -5.0
    assert decoded_data[HUMIDITY] == 42.0


@pytest.mark.parametrize(
    ("raw_temperature", "temperature"),
    [
        pytest.param("135b", -40.0, id="min"),
        pytest.param("125b", None, id="below_min"),
        pytest.param("2382", 60.0, id="above_int16_max"),
        pytest.param("c391", 100.0, id="max"),
        pytest.param("c491", None, id="above_max"),
    ],
)
def test_wave_mini_temperature_bounds(
    raw_temperature: str, temperature: float | None
) -> None:
    """Test Wave Mini temperatures are kept only between -40 and 100 °C."""
    decoded_data = SENSOR_DECODERS[str(CHAR_UUID_WAVEMINI_DATA)](
        bytearray.fromhex(f"1800{raw_temperature}31c168102e000000ff940700ffffffff")
    )

    assert decoded_data[TEMPERATURE] == temperature
