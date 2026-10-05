import logging

import pytest
from airthings_ble import AirthingsBluetoothDeviceData
from airthings_ble.const import (
    CHAR_UUID_DEVICE_NAME,
    CHAR_UUID_FIRMWARE_REV,
    CHAR_UUID_SERIAL_NUMBER_STRING,
)

from fakes import FakeClient, ble_device, device_info_gatt, use_clients

_LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_failed_serial_read_is_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test a serial number that failed to read is read again on the next poll."""
    gatt = device_info_gatt("2930", "G-BLE-1.5.3-master+0")
    second = FakeClient(gatt)
    use_clients(
        monkeypatch,
        FakeClient(gatt, failing={CHAR_UUID_SERIAL_NUMBER_STRING}),
        second,
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    before = await data.update_device(ble_device())
    assert before.identifier == ""

    after = await data.update_device(ble_device())
    assert after.identifier == "123456"
    assert after.manufacturer == "Airthings AS"
    assert second.reads == [
        str(CHAR_UUID_SERIAL_NUMBER_STRING),
        str(CHAR_UUID_FIRMWARE_REV),
    ]


@pytest.mark.asyncio
async def test_populated_device_info_is_not_read_again(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test only the firmware is read again once all device info is known."""
    gatt = device_info_gatt("2930", "G-BLE-1.5.3-master+0")
    second = FakeClient(gatt)
    use_clients(monkeypatch, FakeClient(gatt), second)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    await data.update_device(ble_device())
    after = await data.update_device(ble_device())

    assert after.identifier == "123456"
    assert second.reads == [str(CHAR_UUID_FIRMWARE_REV)]


@pytest.mark.asyncio
async def test_wave_gen_1_identifier_from_name_after_failed_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a Wave Gen 1 picks up its identifier once the name can be read."""
    gatt = device_info_gatt("2900", "1.0.0")
    gatt[CHAR_UUID_SERIAL_NUMBER_STRING] = b"Serial Number"
    gatt[CHAR_UUID_DEVICE_NAME] = b"AT#123456-2900Radon"
    use_clients(
        monkeypatch,
        FakeClient(gatt, failing={CHAR_UUID_DEVICE_NAME}),
        FakeClient(gatt),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    before = await data.update_device(ble_device())
    assert before.identifier == ""
    assert before.name == "Airthings Wave Gen 1"

    after = await data.update_device(ble_device())
    assert after.identifier == "123456"
    assert after.name == "AT#123456-2900Radon"
