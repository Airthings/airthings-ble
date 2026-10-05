import logging

from airthings_ble.const import CHAR_UUID_WAVE_2_DATA, HUMIDITY, TEMPERATURE
from airthings_ble.sensor_decoders import SENSOR_DECODERS, _decode_wave_radon

_LOGGER = logging.getLogger(__name__)


def test_wave_radon_sensor_data() -> None:
    """Test wave plus sensor data."""
    raw_data = bytearray.fromhex("013860f009001100a709ffffffffffff0000ffff")

    decoded_data = _decode_wave_radon(name="Wave2", format_type="<4B8H", scale=1.0)(
        raw_data
    )

    assert decoded_data["humidity"] == 28.0
    assert decoded_data["radon_1day_avg"] == 9
    assert decoded_data["radon_longterm_avg"] == 17
    assert decoded_data["temperature"] == 24.71


def test_wave_radon_sensor_data_below_zero() -> None:
    """Test wave radon temperature below zero."""
    decoded_data = SENSOR_DECODERS[str(CHAR_UUID_WAVE_2_DATA)](
        bytearray.fromhex("013860f0090011000cfeffffffffffff0000ffff")
    )

    assert decoded_data["temperature"] == -5.0
    assert decoded_data["humidity"] == 28.0
    assert decoded_data["radon_1day_avg"] == 9
    assert decoded_data["radon_longterm_avg"] == 17


def test_wave_radon_sensor_data_without_humidity_has_no_temperature() -> None:
    """Test the firmware's invalid reading without humidity gives no temperature."""
    decoded_data = SENSOR_DECODERS[str(CHAR_UUID_WAVE_2_DATA)](
        bytearray.fromhex("01ff3a0025000000ffffffff5a02ffff0000ffff")
    )

    assert decoded_data[HUMIDITY] is None
    assert decoded_data[TEMPERATURE] is None
