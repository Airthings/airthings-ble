import logging

from airthings_ble.command_decode import WaveMiniCommandDecode
from airthings_ble.const import (
    BATTERY,
    HUMIDITY,
    ILLUMINANCE,
    PRESSURE,
    TEMPERATURE,
    VOC,
)
from airthings_ble.sensor_decoders import _decode_wave_mini

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
