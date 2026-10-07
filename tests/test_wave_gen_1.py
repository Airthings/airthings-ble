import logging

import pytest
from airthings_ble import AirthingsBluetoothDeviceData
from airthings_ble.const import (
    CHAR_UUID_TEMPERATURE,
    CHAR_UUID_RADON_1DAYAVG,
    CHAR_UUID_RADON_LONG_TERM_AVG,
    RADON_1DAY_AVG,
    RADON_1DAY_LEVEL,
    RADON_LONGTERM_AVG,
    RADON_LONGTERM_LEVEL,
)
from airthings_ble.sensor_decoders import SENSOR_DECODERS, _decode_wave_illum_accel

from fakes import FakeClient, FakeService, ble_device, device_info_gatt, use_clients

_LOGGER = logging.getLogger(__name__)


def test_wave_gen_1_illuminance_and_accelerometer() -> None:
    """Test Wave Gen 1 illuminance and accelerometer."""
    raw_data = bytearray.fromhex("b20c")

    decoded_data = _decode_wave_illum_accel(
        name="illuminance_accelerometer", format_type="BB", scale=1.0
    )(raw_data)

    assert decoded_data["illuminance"] == 69


@pytest.mark.parametrize(
    ("uuid", "key"),
    [
        (CHAR_UUID_RADON_1DAYAVG, RADON_1DAY_AVG),
        (CHAR_UUID_RADON_LONG_TERM_AVG, RADON_LONGTERM_AVG),
    ],
)
@pytest.mark.parametrize(
    ("raw", "expected"),
    [("6400", 100), ("ff3f", 16383), ("0040", None), ("00ff", None), ("ffff", None)],
)
def test_wave_gen_1_radon(
    uuid: str, key: str, raw: str, expected: float | None
) -> None:
    """Test Wave Gen 1 radon values, with sentinel values rejected."""
    assert SENSOR_DECODERS[str(uuid)](bytearray.fromhex(raw)) == {key: expected}


@pytest.mark.asyncio
async def test_wave_gen_1_radon_sentinel_has_no_level(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a Wave Gen 1 radon sentinel is reported without a radon level."""
    gatt = device_info_gatt("2900", "1.0.0")
    gatt[CHAR_UUID_RADON_1DAYAVG] = bytes.fromhex("ffff")
    gatt[CHAR_UUID_RADON_LONG_TERM_AVG] = bytes.fromhex("6400")
    use_clients(
        monkeypatch,
        FakeClient(
            gatt,
            [FakeService([CHAR_UUID_RADON_1DAYAVG, CHAR_UUID_RADON_LONG_TERM_AVG])],
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert device.sensors == {
        RADON_1DAY_AVG: None,
        RADON_LONGTERM_AVG: 100,
        RADON_LONGTERM_LEVEL: "fair",
    }
    assert RADON_1DAY_LEVEL not in device.sensors


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("60f0", -40.0),
        ("5ff0", None),
        ("0ffb", -12.65),
        ("1027", 100.0),
        ("1127", None),
        ("0080", None),
    ],
)
def test_wave_gen_1_temperature_range(raw: str, expected: float | None) -> None:
    """Test Wave Gen 1 temperatures outside -40 to 100 °C are rejected."""
    decoded = SENSOR_DECODERS[str(CHAR_UUID_TEMPERATURE)](bytearray.fromhex(raw))

    assert decoded == {"temperature": expected}
