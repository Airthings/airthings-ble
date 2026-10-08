import asyncio
import logging

import pytest
from airthings_ble import (
    AirthingsBluetoothDeviceData,
    DisconnectedError,
    UnsupportedDeviceError,
    parser,
)
from airthings_ble.const import CHAR_UUID_FIRMWARE_REV, CHAR_UUID_MODEL_NUMBER_STRING
from bleak import BleakError

from fakes import FakeClient, ble_device, device_info_gatt, use_clients

_LOGGER = logging.getLogger(__name__)
_WAVE_PLUS = device_info_gatt("2930", "G-BLE-1.5.3-master+0")


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["Airthings Renew", "Airthings View Plus"])
async def test_unsupported_name_is_rejected_without_connecting(
    monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    """Test a device named as an unsupported product is rejected up front."""
    use_clients(monkeypatch)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    with pytest.raises(UnsupportedDeviceError, match=name):
        await data.update_device(ble_device(name))


@pytest.mark.asyncio
async def test_unsupported_model_disconnects(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test a device with an unsupported model code is disconnected."""
    client = FakeClient(device_info_gatt("3219", "X-1.0.0"))
    use_clients(monkeypatch, client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER, max_attempts=2)

    with pytest.raises(UnsupportedDeviceError):
        await data.update_device(ble_device("Airthings Wave"))

    assert client.disconnected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("message", "cache_cleared"),
    [
        (f"Characteristic {CHAR_UUID_MODEL_NUMBER_STRING} was not found!", True),
        ("Not connected", False),
    ],
)
async def test_missing_characteristic_clears_cache(
    monkeypatch: pytest.MonkeyPatch, message: str, cache_cleared: bool
) -> None:
    """Test only a characteristic-not-found error clears the service cache."""
    client = FakeClient(
        _WAVE_PLUS,
        failing={CHAR_UUID_MODEL_NUMBER_STRING},
        read_error=BleakError(message),
    )
    use_clients(monkeypatch, client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    with pytest.raises(BleakError, match=message):
        await data.update_device(ble_device())

    assert client.cache_cleared is cache_cleared
    assert client.disconnected


@pytest.mark.asyncio
async def test_disconnect_during_update_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a disconnect mid-update interrupts it with DisconnectedError."""
    client = FakeClient(_WAVE_PLUS, disconnect_on_read=CHAR_UUID_FIRMWARE_REV)
    use_clients(monkeypatch, client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    with pytest.raises(DisconnectedError):
        await data.update_device(ble_device())

    assert client.disconnected
    assert data.device_info.did_first_sync is False


@pytest.mark.asyncio
async def test_disconnect_during_update_is_retried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test an update interrupted by a disconnect is retried."""
    use_clients(
        monkeypatch,
        FakeClient(_WAVE_PLUS, disconnect_on_read=CHAR_UUID_FIRMWARE_REV),
        FakeClient(_WAVE_PLUS),
    )
    monkeypatch.setattr(parser, "UPDATE_TIMEOUT", 60)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)
    data.set_max_attempts(2)

    async with asyncio.timeout(5):
        device = await data.update_device(ble_device())

    assert device.sw_version == "G-BLE-1.5.3-master+0"


@pytest.mark.asyncio
async def test_bleak_error_on_final_attempt_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a BleakError on every attempt is raised from the last one."""
    use_clients(
        monkeypatch,
        FakeClient(_WAVE_PLUS, failing={CHAR_UUID_MODEL_NUMBER_STRING}),
        FakeClient(
            _WAVE_PLUS,
            failing={CHAR_UUID_MODEL_NUMBER_STRING},
            read_error=BleakError("second attempt"),
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER, max_attempts=2)

    with pytest.raises(BleakError, match="^second attempt$"):
        await data.update_device(ble_device())


@pytest.mark.asyncio
async def test_no_attempts_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test an update allowed no attempts fails instead of returning nothing."""
    use_clients(monkeypatch)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER, max_attempts=0)

    with pytest.raises(RuntimeError):
        await data.update_device(ble_device())
