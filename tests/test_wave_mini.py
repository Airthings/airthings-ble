import logging

import pytest
from airthings_ble.command_decode import WaveMiniCommandDecode
from airthings_ble.const import (
    BATTERY,
    BLE_VERSION,
    CHAR_UUID_WAVEMINI_DATA,
    HUMIDITY,
    ILLUMINANCE,
    PRESSURE,
    SUB_VERSION,
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
    ) == {BATTERY: 3.0, BLE_VERSION: None, SUB_VERSION: None}


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


def test_wave_mini_sensor_data_before_first_measurement() -> None:
    """Test Wave Mini values that are not measured yet are dropped."""
    decoded_data = SENSOR_DECODERS[str(CHAR_UUID_WAVEMINI_DATA)](
        bytearray.fromhex("ffffffffffffffffffffffffffffffffffffffff")
    )

    assert decoded_data[ILLUMINANCE] is None
    assert decoded_data[TEMPERATURE] is None
    assert decoded_data[PRESSURE] is None
    assert decoded_data[HUMIDITY] is None
    assert decoded_data[VOC] is None


@pytest.mark.parametrize(
    ("raw_illuminance", "illuminance"),
    [
        pytest.param("ffff", None, id="not_measured"),
        pytest.param("ff00", 100, id="max"),
        pytest.param("feff", 99, id="high_byte_set"),
        pytest.param("1800", 9, id="normal"),
    ],
)
def test_wave_mini_illuminance(raw_illuminance: str, illuminance: int | None) -> None:
    """Test Wave Mini illuminance is dropped only when it is not measured yet."""
    decoded_data = SENSOR_DECODERS[str(CHAR_UUID_WAVEMINI_DATA)](
        bytearray.fromhex(f"{raw_illuminance}327431c168102e000000ff940700ffffffff")
    )

    assert decoded_data[ILLUMINANCE] == illuminance


@pytest.mark.parametrize(
    ("raw_pressure", "pressure"),
    [
        pytest.param("ffff", None, id="not_measured"),
        pytest.param("feff", 1310.68, id="max"),
        pytest.param("31c1", 989.14, id="normal"),
    ],
)
def test_wave_mini_pressure(raw_pressure: str, pressure: float | None) -> None:
    """Test Wave Mini pressure is dropped only when it is not measured yet."""
    decoded_data = SENSOR_DECODERS[str(CHAR_UUID_WAVEMINI_DATA)](
        bytearray.fromhex(f"18003274{raw_pressure}68102e000000ff940700ffffffff")
    )

    assert decoded_data[PRESSURE] == pressure
