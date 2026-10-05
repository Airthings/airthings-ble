import logging
from typing import Any
from uuid import UUID

import pytest
from airthings_ble import AirthingsBluetoothDeviceData, AirthingsDeviceType
from airthings_ble.const import (
    CHAR_UUID_DATETIME,
    CHAR_UUID_HARDWARE_REV,
    CHAR_UUID_HUMIDITY,
    CHAR_UUID_ILLUMINANCE_ACCELEROMETER,
    CHAR_UUID_RADON_1DAYAVG,
    CHAR_UUID_RADON_LONG_TERM_AVG,
    CHAR_UUID_TEMPERATURE,
    CHAR_UUID_WAVE_2_DATA,
    CHAR_UUID_WAVE_PLUS_DATA,
    CHAR_UUID_WAVEMINI_DATA,
    COMMAND_UUID_WAVE_2,
    COMMAND_UUID_WAVE_MINI,
    COMMAND_UUID_WAVE_PLUS,
)

from fakes import FakeClient, FakeService, ble_device, device_info_gatt, use_clients

_LOGGER = logging.getLogger(__name__)

_WAVE_PLUS_DATA = "01380d800b002200bd094cc31d036c0000007d05"
_WAVE_RADON_DATA = "013860f009001100a709ffffffffffff0000ffff"
_WAVE_MINI_DATA = "1800327431c168102e000000ff940700ffffffff"
_WAVE_PLUS_COMMAND = "6d00600c04000100008211ff00000000c04c20001f3560007006B80B0900"
_WAVE_MINI_COMMAND = (
    "6d0064000000c800000001020304f4015802bc02000020038403b80b4c04b0040000"
)
_UNRELATED_CHARACTERISTIC = UUID("b42e0000-ade7-11e4-89d3-123b93f75cba")


def _wave_client(
    model: str,
    data_uuid: UUID,
    data: str,
    command_uuid: UUID,
    command: str,
    **kwargs: Any,
) -> FakeClient:
    gatt = device_info_gatt(model, "G-BLE-1.5.3-master+0")
    gatt[data_uuid] = bytes.fromhex(data)
    return FakeClient(
        gatt,
        [FakeService([data_uuid, command_uuid])],
        command_response=bytes.fromhex(command),
        **kwargs,
    )


@pytest.mark.asyncio
async def test_wave_plus_update(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test a Wave Plus reports its sensor data and battery from the command."""
    use_clients(
        monkeypatch,
        _wave_client(
            "2930",
            CHAR_UUID_WAVE_PLUS_DATA,
            _WAVE_PLUS_DATA,
            COMMAND_UUID_WAVE_PLUS,
            _WAVE_PLUS_COMMAND,
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert device.model == AirthingsDeviceType.WAVE_PLUS
    assert device.sensors == {
        "humidity": 28.0,
        "illuminance": 5,
        "radon_1day_avg": 11,
        "radon_1day_level": "good",
        "radon_longterm_avg": 34,
        "radon_longterm_level": "good",
        "temperature": 24.93,
        "pressure": 999.92,
        "co2": 797.0,
        "voc": 108.0,
        "battery": 100,
    }


@pytest.mark.asyncio
async def test_wave_radon_update(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test a Wave Radon reports its sensor data and battery from the command."""
    use_clients(
        monkeypatch,
        _wave_client(
            "2950",
            CHAR_UUID_WAVE_2_DATA,
            _WAVE_RADON_DATA,
            COMMAND_UUID_WAVE_2,
            _WAVE_PLUS_COMMAND,
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert device.model == AirthingsDeviceType.WAVE_RADON
    assert device.sensors == {
        "illuminance": 37,
        "humidity": 28.0,
        "radon_1day_avg": 9,
        "radon_1day_level": "good",
        "radon_longterm_avg": 17,
        "radon_longterm_level": "good",
        "temperature": 24.71,
        "battery": 100,
    }


@pytest.mark.asyncio
async def test_wave_mini_update(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test a Wave Mini reports its sensor data and three-battery percentage."""
    use_clients(
        monkeypatch,
        _wave_client(
            "2920",
            CHAR_UUID_WAVEMINI_DATA,
            _WAVE_MINI_DATA,
            COMMAND_UUID_WAVE_MINI,
            _WAVE_MINI_COMMAND,
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert device.model == AirthingsDeviceType.WAVE_MINI
    assert device.sensors == {
        "illuminance": 9,
        "temperature": 24.31,
        "pressure": 989.14,
        "humidity": 42.0,
        "voc": 46.0,
        "battery": 15,
    }


@pytest.mark.asyncio
async def test_wave_radon_in_pci(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test Wave radon is converted to pCi/L while its level stays Bq/m3 based."""
    use_clients(
        monkeypatch,
        _wave_client(
            "2930",
            CHAR_UUID_WAVE_PLUS_DATA,
            "01380d80a0000001bd094cc31d036c0000007d05",
            COMMAND_UUID_WAVE_PLUS,
            _WAVE_PLUS_COMMAND,
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER, is_metric=False)

    device = await data.update_device(ble_device())

    assert device.sensors["radon_1day_avg"] == pytest.approx(160 * 0.027)
    assert device.sensors["radon_1day_level"] == "poor"
    assert device.sensors["radon_longterm_avg"] == pytest.approx(256 * 0.027)
    assert device.sensors["radon_longterm_level"] == "poor"


def _wave_gen_1_gatt() -> dict[UUID, bytes]:
    gatt = device_info_gatt("2900", "1.0.0")
    gatt[CHAR_UUID_DATETIME] = bytes.fromhex("e8070a060c1e00")
    gatt[CHAR_UUID_TEMPERATURE] = bytes.fromhex("0cfe")
    gatt[CHAR_UUID_HUMIDITY] = bytes.fromhex("c611")
    gatt[CHAR_UUID_RADON_1DAYAVG] = bytes.fromhex("7800")
    gatt[CHAR_UUID_RADON_LONG_TERM_AVG] = bytes.fromhex("2200")
    gatt[CHAR_UUID_ILLUMINANCE_ACCELEROMETER] = bytes.fromhex("b20c")
    return gatt


_WAVE_GEN_1_SENSOR_UUIDS = [
    CHAR_UUID_DATETIME,
    CHAR_UUID_TEMPERATURE,
    CHAR_UUID_HUMIDITY,
    CHAR_UUID_RADON_1DAYAVG,
    CHAR_UUID_RADON_LONG_TERM_AVG,
    CHAR_UUID_ILLUMINANCE_ACCELEROMETER,
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("is_metric", "radon_1day", "radon_longterm"),
    [(True, 120, 34), (False, 120 * 0.027, 34 * 0.027)],
)
async def test_wave_gen_1_update(
    monkeypatch: pytest.MonkeyPatch,
    is_metric: bool,
    radon_1day: float,
    radon_longterm: float,
) -> None:
    """Test a Wave Gen 1 reads one characteristic per sensor and drops the clock."""
    client = FakeClient(_wave_gen_1_gatt(), [FakeService(_WAVE_GEN_1_SENSOR_UUIDS)])
    use_clients(monkeypatch, client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER, is_metric=is_metric)

    device = await data.update_device(ble_device())

    assert device.model == AirthingsDeviceType.WAVE_GEN_1
    assert device.hw_version == ""
    assert str(CHAR_UUID_HARDWARE_REV) not in client.reads
    assert device.sensors == {
        "temperature": -5.0,
        "humidity": 45.5,
        "radon_1day_avg": pytest.approx(radon_1day),
        "radon_1day_level": "fair",
        "radon_longterm_avg": pytest.approx(radon_longterm),
        "radon_longterm_level": "good",
        "illuminance": 69,
        "accelerometer": "12.0",
    }


@pytest.mark.asyncio
async def test_failed_sensor_read_is_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test a sensor characteristic that fails to read leaves the others intact."""
    use_clients(
        monkeypatch,
        FakeClient(
            _wave_gen_1_gatt(),
            [FakeService(_WAVE_GEN_1_SENSOR_UUIDS)],
            failing={CHAR_UUID_TEMPERATURE},
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert "temperature" not in device.sensors
    assert device.sensors["humidity"] == 45.5


@pytest.mark.asyncio
async def test_unrelated_characteristic_is_not_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a characteristic that is not a known sensor is ignored."""
    gatt = device_info_gatt("2930", "G-BLE-1.5.3-master+0")
    gatt[CHAR_UUID_WAVE_PLUS_DATA] = bytes.fromhex(_WAVE_PLUS_DATA)
    client = FakeClient(
        gatt, [FakeService([_UNRELATED_CHARACTERISTIC, CHAR_UUID_WAVE_PLUS_DATA])]
    )
    use_clients(monkeypatch, client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert str(_UNRELATED_CHARACTERISTIC) not in client.reads
    assert device.sensors["co2"] == 797.0


@pytest.mark.asyncio
@pytest.mark.command_timeout
async def test_wave_command_timeout_keeps_sensor_data(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Test an unanswered Wave command gives no battery but keeps sensor data."""
    monkeypatch.setattr("airthings_ble.parser.COMMAND_TIMEOUT", 0.01)
    client = _wave_client(
        "2930",
        CHAR_UUID_WAVE_PLUS_DATA,
        _WAVE_PLUS_DATA,
        COMMAND_UUID_WAVE_PLUS,
        _WAVE_PLUS_COMMAND,
        silent_commands=True,
    )
    use_clients(monkeypatch, client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert "Timeout getting command data" in caplog.text
    assert "battery" not in device.sensors
    assert device.sensors["co2"] == 797.0
    assert not client.notifying


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("response", "message"),
    [
        (
            "6e00600c04000100008211ff00000000c04c20001f3560007006B80B0900",
            "Result for wrong command received, expected 6d got 6e",
        ),
        (
            "6d00600c04000100008211ff00000000c04c20001f3560007006B80B090000",
            "Wrong length data received (29) versus expected (28)",
        ),
    ],
)
async def test_rejected_wave_command_response_gives_no_battery(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    response: str,
    message: str,
) -> None:
    """Test a Wave command response that fails validation gives no battery."""
    use_clients(
        monkeypatch,
        _wave_client(
            "2930",
            CHAR_UUID_WAVE_PLUS_DATA,
            _WAVE_PLUS_DATA,
            COMMAND_UUID_WAVE_PLUS,
            response,
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert message in caplog.text
    assert "battery" not in device.sensors
    assert device.sensors["co2"] == 797.0
