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

_WAVE_PLUS_COMMAND_RESPONSE = bytes.fromhex(
    "6d00600c04000100008211ff00000000c04c20001f3560007006B80B0900"
)

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
    assert client.stop_notify_calls == 1
    assert client.disconnected


@pytest.mark.asyncio
@pytest.mark.parametrize(("model", "firmware", "service"), [_ATOM, _WAVE_PLUS])
@pytest.mark.parametrize(
    "error", [OSError("stop failed"), ValueError("notification never started")]
)
async def test_failing_stop_notify_keeps_the_timeout(
    monkeypatch: pytest.MonkeyPatch,
    model: str,
    firmware: str,
    service: Callable[[], FakeService],
    error: Exception,
) -> None:
    """Test a backend error while cleaning up does not replace the timeout."""
    monkeypatch.setattr("airthings_ble.parser.UPDATE_TIMEOUT", 0.05)
    client = FakeClient(
        device_info_gatt(model, firmware),
        [service()],
        stall_write=True,
        stop_notify_error=error,
    )
    use_clients(monkeypatch, client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    with pytest.raises(TimeoutError):
        await data.update_device(ble_device())

    assert client.stop_notify_calls == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(("model", "firmware", "service"), [_ATOM, _WAVE_PLUS])
async def test_stop_notify_failure_fails_the_update(
    monkeypatch: pytest.MonkeyPatch,
    model: str,
    firmware: str,
    service: Callable[[], FakeService],
) -> None:
    """Test a failing stop_notify after a good command fails the update."""
    use_clients(
        monkeypatch,
        FakeClient(
            device_info_gatt(model, firmware),
            [service()],
            stop_notify_error=BleakError("stop failed"),
            command_response=_WAVE_PLUS_COMMAND_RESPONSE if model == "2930" else None,
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    with pytest.raises(BleakError, match="^stop failed$"):
        await data.update_device(ble_device())


@pytest.mark.asyncio
async def test_stop_notify_failure_is_retried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a failing stop_notify reconnects instead of reusing the client."""
    model, firmware, service = _ATOM
    first = FakeClient(
        device_info_gatt(model, firmware),
        [service()],
        stop_notify_error=BleakError("stop failed"),
    )
    second = FakeClient(device_info_gatt(model, firmware), [service()])
    use_clients(monkeypatch, first, second)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER, max_attempts=2)

    device = await data.update_device(ble_device())

    assert device.sensors["battery"] is not None
    assert first.disconnected
