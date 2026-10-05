import asyncio
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


@pytest.mark.asyncio
@pytest.mark.parametrize(("model", "firmware", "service"), [_ATOM, _WAVE_PLUS])
async def test_stalled_stop_notify_does_not_outlive_timeout(
    monkeypatch: pytest.MonkeyPatch,
    model: str,
    firmware: str,
    service: Callable[[], FakeService],
) -> None:
    """Test a hanging stop_notify cannot keep a timed out update alive."""
    monkeypatch.setattr("airthings_ble.parser.UPDATE_TIMEOUT", 0.05)
    monkeypatch.setattr("airthings_ble.parser.STOP_NOTIFY_TIMEOUT", 0.05)
    client = FakeClient(
        device_info_gatt(model, firmware),
        [service()],
        stall_write=True,
        stall_stop_notify=True,
    )
    use_clients(monkeypatch, client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    task = asyncio.create_task(data.update_device(ble_device()))
    await asyncio.sleep(0.5)

    assert task.done()
    assert isinstance(task.exception(), TimeoutError)
    assert client.disconnected
