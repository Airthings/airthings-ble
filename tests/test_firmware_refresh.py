import logging

import pytest
from airthings_ble import AirthingsBluetoothDeviceData
from airthings_ble.const import CHAR_UUID_FIRMWARE_REV

from fakes import FakeClient, atom_service, ble_device, device_info_gatt, use_clients

_LOGGER = logging.getLogger(__name__)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("model", "old_firmware", "old_version", "new_firmware", "new_version"),
    [
        ("3210", "T-SUB-2.6.0-master+0", (2, 6, 0), "T-SUB-3.0.1-master+0", (3, 0, 1)),
        ("3220", "T-SUB-2.6.0-master+0", (2, 6, 0), "T-SUB-3.0.3-master+0", (3, 0, 3)),
        ("3250", "R-SUB-1.3.3-master+0", (1, 3, 3), "R-SUB-1.3.5-master+0", (1, 3, 5)),
    ],
)
async def test_atom_firmware_refreshes_between_polls(
    monkeypatch: pytest.MonkeyPatch,
    model: str,
    old_firmware: str,
    old_version: tuple[int, int, int],
    new_firmware: str,
    new_version: tuple[int, int, int],
) -> None:
    """Test a firmware upgrade between two polls is picked up on the second one."""
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)
    use_clients(
        monkeypatch,
        FakeClient(device_info_gatt(model, old_firmware), [atom_service()]),
        FakeClient({CHAR_UUID_FIRMWARE_REV: new_firmware.encode()}, [atom_service()]),
    )

    before = await data.update_device(ble_device())
    assert before.sw_version == old_firmware
    assert before.firmware.current_version == old_version
    assert before.firmware.need_firmware_upgrade is True
    assert before.sensors["battery"] is not None

    after = await data.update_device(ble_device())
    assert after.sw_version == new_firmware
    assert after.firmware.current_version == new_version
    assert after.firmware.need_firmware_upgrade is False


@pytest.mark.asyncio
async def test_wave_plus_firmware_refreshes_between_polls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test the Wave Plus firmware string follows the device across polls."""
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)
    use_clients(
        monkeypatch,
        FakeClient(device_info_gatt("2930", "G-BLE-1.5.3-master+0")),
        FakeClient({CHAR_UUID_FIRMWARE_REV: b"G-BLE-2.2.3-master+0"}),
    )

    before = await data.update_device(ble_device())
    assert before.sw_version == "G-BLE-1.5.3-master+0"

    after = await data.update_device(ble_device())
    assert after.sw_version == "G-BLE-2.2.3-master+0"
    assert data.device_info.sw_version == "G-BLE-2.2.3-master+0"
