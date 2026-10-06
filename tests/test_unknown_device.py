import logging

import pytest
from airthings_ble import AirthingsBluetoothDeviceData, AirthingsDeviceType
from airthings_ble.const import CHAR_UUID_MODEL_NUMBER_STRING
from airthings_ble.parser import UnsupportedDeviceError
from bleak import BleakError

from fakes import ADDRESS, FakeClient, ble_device, device_info_gatt, use_clients

_LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_model_read_failure_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test a failed model read fails the update instead of returning UNKNOWN."""
    client = FakeClient(
        device_info_gatt("2930", "G-BLE-1.5.3-master+0"),
        failing={CHAR_UUID_MODEL_NUMBER_STRING},
    )
    use_clients(monkeypatch, client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    with pytest.raises(BleakError):
        await data.update_device(ble_device())

    assert client.disconnected
    assert data.device_info.did_first_sync is False


@pytest.mark.asyncio
async def test_model_read_failure_is_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test a failed model read is retried and the next attempt is used."""
    use_clients(
        monkeypatch,
        FakeClient(
            device_info_gatt("2930", "G-BLE-1.5.3-master+0"),
            failing={CHAR_UUID_MODEL_NUMBER_STRING},
        ),
        FakeClient(device_info_gatt("2930", "G-BLE-1.5.3-master+0")),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER, max_attempts=2)

    device = await data.update_device(ble_device())

    assert device.model == AirthingsDeviceType.WAVE_PLUS
    assert device.address == ADDRESS
    assert device.name == "Airthings device"
    assert device.identifier == "123456"
    assert data.device_info.did_first_sync is True


@pytest.mark.asyncio
async def test_unknown_model_code_is_unsupported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test an unknown model code is rejected without changing shared state."""
    client = FakeClient(device_info_gatt("3219", "X-1.0.0"))
    use_clients(monkeypatch, client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    with pytest.raises(UnsupportedDeviceError, match="3219"):
        await data.update_device(ble_device())

    assert client.disconnected
    assert AirthingsDeviceType.UNKNOWN.raw_value == "0"
    assert data.device_info.did_first_sync is False


def test_from_raw_value_does_not_mutate_members() -> None:
    """Test looking up an unknown model code leaves the enum untouched."""
    assert AirthingsDeviceType.from_raw_value("1234") is AirthingsDeviceType.UNKNOWN
    assert AirthingsDeviceType.UNKNOWN.raw_value == "0"
    assert AirthingsDeviceType.WAVE_PLUS.raw_value == "2930"
