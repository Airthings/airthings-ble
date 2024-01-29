import logging

import pytest

from airthings_ble.parser import (
    WaveMiniCommandDecode,
    WaveRadonAndPlusCommandDecode,
    _decode_wave_illum_accel,
    _decode_wave_mini,
    _decode_wave_plus,
    _decode_wave_radon,
    get_absolute_pressure,
    get_radon_level,
)

_LOGGER = logging.getLogger(__name__)


def test_wave_plus_command_decode():
    """Test wave plus command decode."""
    decode = WaveRadonAndPlusCommandDecode()
    assert decode.decode_data(
        logger=_LOGGER,
        raw_data=bytearray.fromhex(
            "6d00600c04000100008211ff00000000c04c20001f3560007006B80B0900"
        ),
    ) == {"battery": 3.0}


def test_wave_plus_sensor_data():
    """Test wave plus sensor data."""
    raw_data = bytearray.fromhex("01380d800b002200bd094cc31d036c0000007d05")

    # Call the function
    decoded_data = _decode_wave_plus(name="Plus", format_type="<4B8H", scale=1.0)(
        raw_data
    )

    assert decoded_data["humidity"] == 28.0
    assert decoded_data["radon_1day_avg"] == 11
    assert decoded_data["radon_longterm_avg"] == 34
    assert decoded_data["temperature"] == 24.93
    assert decoded_data["voc"] == 108
    assert decoded_data["co2"] == 797
    assert decoded_data["illuminance_pct"] == 13
    assert decoded_data["rel_atm_pressure"] == 999.92


def test_wave_radon_sensor_data():
    """Test wave plus sensor data."""
    raw_data = bytearray.fromhex("013860f009001100a709ffffffffffff0000ffff")

    decoded_data = _decode_wave_radon(name="Wave2", format_type="<4B8H", scale=1.0)(
        raw_data
    )

    assert decoded_data["humidity"] == 28.0
    assert decoded_data["radon_1day_avg"] == 9
    assert decoded_data["radon_longterm_avg"] == 17
    assert decoded_data["temperature"] == 24.71


def test_wave_mini_command_decode():
    """Test wave Mini command decode."""
    decode = WaveMiniCommandDecode()
    assert decode.decode_data(
        logger=_LOGGER,
        raw_data=bytearray.fromhex(
            "6d00d595000000090002030407070a00ffff0013000224008e0094110700ffffffff"
        ),
    ) == {"battery": 4.5}


def test_wave_mini_sensor_data():
    """Test Wave Mini sensor data."""
    raw_data = bytearray.fromhex("6f00977470c30d0b2d010200fefa0700ffffffff")

    decoded_data = _decode_wave_mini(name="WaveMini", format_type="<2B5HLL", scale=1.0)(
        raw_data
    )

    assert decoded_data["humidity"] == 28.29
    assert decoded_data["rel_atm_pressure"] == 1000.64
    assert decoded_data["temperature"] == 25.32
    assert decoded_data["voc"] == 301.0
    assert decoded_data["rel_atm_pressure"] == 1000.64


def test_wave_gen_1_illuminance_and_accelerometer():
    """Test Wave Gen 1 illuminance and accelerometer."""
    raw_data = bytearray.fromhex("b20c")

    decoded_data = _decode_wave_illum_accel(
        name="illuminance_accelerometer", format_type="BB", scale=1.0
    )(raw_data)

    assert decoded_data["illuminance"] == 178.0
