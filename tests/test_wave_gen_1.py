from airthings_ble.sensor_decoders import _decode_wave_illum_accel


def test_wave_gen_1_illuminance_and_accelerometer() -> None:
    """Test Wave Gen 1 illuminance and accelerometer."""
    raw_data = bytearray.fromhex("b20c")

    decoded_data = _decode_wave_illum_accel(
        name="illuminance_accelerometer", format_type="BB", scale=1.0
    )(raw_data)

    assert decoded_data["illuminance"] == 69
