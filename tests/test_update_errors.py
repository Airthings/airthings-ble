import logging

import pytest
from airthings_ble import AirthingsBluetoothDeviceData
from airthings_ble.const import CHAR_UUID_MODEL_NUMBER_STRING
from bleak import BleakError

from fakes import FakeClient, ble_device, device_info_gatt, use_clients

_LOGGER = logging.getLogger(__name__)
_WAVE_PLUS = device_info_gatt("2930", "G-BLE-1.5.3-master+0")


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
