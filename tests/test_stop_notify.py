import logging
from typing import Callable

import pytest
from airthings_ble import AirthingsBluetoothDeviceData
from airthings_ble.const import COMMAND_UUID_WAVE_PLUS
from bleak import BleakError

from fakes import (
    FakeClient,
    FakeService,
    atom_service,
    ble_device,
    device_info_gatt,
    use_clients,
)

_LOGGER = logging.getLogger(__name__)

_ATOM = ("3220", "T-SUB-3.0.3-master+0", atom_service)
_WAVE_PLUS = (
    "2930",
    "G-BLE-1.5.3-master+0",
    lambda: FakeService([COMMAND_UUID_WAVE_PLUS]),
)


@pytest.mark.asyncio
@pytest.mark.parametrize(("model", "firmware", "service"), [_ATOM, _WAVE_PLUS])
async def test_notifications_stopped_when_write_fails(
    monkeypatch: pytest.MonkeyPatch,
    model: str,
    firmware: str,
    service: Callable[[], FakeService],
) -> None:
    """Test notifications are stopped when the command write fails."""
    client = FakeClient(
        device_info_gatt(model, firmware),
        [service()],
        write_error=BleakError("write failed"),
    )
    use_clients(monkeypatch, client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    with pytest.raises(BleakError, match="^write failed$"):
        await data.update_device(ble_device())

    assert not client.notifying


@pytest.mark.asyncio
@pytest.mark.parametrize(("model", "firmware", "service"), [_ATOM, _WAVE_PLUS])
async def test_stop_notify_failure_keeps_original_error(
    monkeypatch: pytest.MonkeyPatch,
    model: str,
    firmware: str,
    service: Callable[[], FakeService],
) -> None:
    """Test a failing stop_notify does not mask the command write error."""
    use_clients(
        monkeypatch,
        FakeClient(
            device_info_gatt(model, firmware),
            [service()],
            write_error=BleakError("write failed"),
            stop_notify_error=BleakError("stop failed"),
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    with pytest.raises(BleakError, match="^write failed$"):
        await data.update_device(ble_device())
