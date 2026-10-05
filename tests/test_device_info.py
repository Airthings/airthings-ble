import logging

import pytest
from airthings_ble import AirthingsBluetoothDeviceData
from airthings_ble.const import CHAR_UUID_DEVICE_NAME, CHAR_UUID_SERIAL_NUMBER_STRING
from airthings_ble.parser import short_address

from fakes import FakeClient, ble_device, device_info_gatt, use_clients

_LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("name", "identifier"),
    [
        ("AT#123456-2900Radon", "123456"),
        ("AT#12345-2900Radon", ""),
        ("Airthings Wave", ""),
    ],
)
async def test_wave_gen_1_identifier_from_name(
    monkeypatch: pytest.MonkeyPatch, name: str, identifier: str
) -> None:
    """Test a Wave Gen 1 only takes a six digit serial number from its name."""
    gatt = device_info_gatt("2900", "1.0.0")
    gatt[CHAR_UUID_SERIAL_NUMBER_STRING] = b"Serial Number"
    gatt[CHAR_UUID_DEVICE_NAME] = name.encode()
    use_clients(monkeypatch, FakeClient(gatt))
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert device.identifier == identifier
    assert device.name == name


@pytest.mark.asyncio
async def test_serial_number_placeholder_is_ignored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test the "Serial Number" placeholder macOS reports is not an identifier."""
    gatt = device_info_gatt("2930", "G-BLE-1.5.3-master+0")
    gatt[CHAR_UUID_SERIAL_NUMBER_STRING] = b"Serial Number"
    gatt[CHAR_UUID_DEVICE_NAME] = b""
    use_clients(monkeypatch, FakeClient(gatt))
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert device.identifier == ""
    assert device.name == "Airthings Wave Plus"
    assert device.manufacturer == "Airthings AS"
    assert device.hw_version == "REV A"


@pytest.mark.parametrize(
    "address",
    ["aa:bb:cc:dd:ee:ff", "AA-BB-CC-DD-EE-FF", "aabbccddeeff"],
)
def test_short_address(address: str) -> None:
    """Test the short address is the last three bytes in upper case."""
    assert short_address(address) == "DDEEFF"
