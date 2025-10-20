import logging

from airthings_ble.parser import WaveMiniCommandDecode, _decode_wave_mini

_LOGGER = logging.getLogger(__name__)


def test_wave_mini_command_decode() -> None:
    """Test wave plus command decode."""
    decode = WaveMiniCommandDecode()
    assert decode.decode_data(
        logger=_LOGGER,
        raw_data=bytearray.fromhex(
            "6d00600c04000100008211ff00000000c04c20001f3560007006B80B0900"
        ),
    ) == {"battery": 3.0}


def test_wave_mini_sensor_data() -> None:
    """Test wave mini sensor data."""
    raw_data = bytearray.fromhex("01380d800b002200bd094cc31d036c0000007d05")

    decoded_data = _decode_wave_mini(name="Mini", format_type="<4B8H", scale=1.0)(
        raw_data
    )

    assert decoded_data["humidity"] == 28.0
    assert decoded_data["temperature"] == 24.93
    assert decoded_data["voc"] == 108
    assert decoded_data["pressure"] == 999.92
