import logging

import pytest
from airthings_ble.const import CHAR_UUID_WAVE_2_DATA, TEMPERATURE
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


@pytest.mark.parametrize(
    ("raw_temperature", "temperature"),
    [
        pytest.param("60f0", -40.0, id="min"),
        pytest.param("5ff0", None, id="below_min"),
        pytest.param("1027", 100.0, id="max"),
        pytest.param("1127", None, id="above_max"),
    ],
)
def test_wave_radon_temperature_bounds(
    raw_temperature: str, temperature: float | None
) -> None:
    """Test wave radon temperatures are kept only between -40 and 100 °C."""
    decoded_data = SENSOR_DECODERS[str(CHAR_UUID_WAVE_2_DATA)](
        bytearray.fromhex(f"013860f009001100{raw_temperature}ffffffffffff0000ffff")
    )

    assert decoded_data[TEMPERATURE] == temperature
