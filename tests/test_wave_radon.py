import logging

from airthings_ble.parser import _decode_wave_radon

_LOGGER = logging.getLogger(__name__)


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
