import asyncio
import logging
from typing import Any

import pytest
from airthings_ble import AirthingsBluetoothDeviceData
from airthings_ble.command_decode import NotificationReceiver
from airthings_ble.const import CHAR_UUID_FIRMWARE_REV

from fakes import FakeClient, atom_service, ble_device, device_info_gatt, use_clients

_LOGGER = logging.getLogger(__name__)


class SilentClient(FakeClient):
    async def write_gatt_char(self, characteristic: Any, data: bytearray) -> None:
        pass


@pytest.mark.asyncio
async def test_outdated_firmware_is_logged_once(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Test an outdated firmware warning is not repeated on every poll."""
    use_clients(
        monkeypatch,
        FakeClient(device_info_gatt("3210", "T-SUB-2.6.0-master+0"), [atom_service()]),
        FakeClient({CHAR_UUID_FIRMWARE_REV: b"T-SUB-2.6.0-master+0"}, [atom_service()]),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    with caplog.at_level(logging.DEBUG):
        await data.update_device(ble_device())
        await data.update_device(ble_device())

    warnings = [
        record
        for record in caplog.records
        if record.levelno == logging.WARNING and "not up to date" in record.message
    ]
    assert len(warnings) == 1


@pytest.mark.asyncio
@pytest.mark.command_timeout
async def test_command_timeout_is_not_a_warning(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Test a command that gets no response is logged at debug level."""

    async def time_out(self: NotificationReceiver, timeout: float) -> None:
        raise asyncio.TimeoutError

    monkeypatch.setattr(NotificationReceiver, "wait_for_message", time_out)
    use_clients(
        monkeypatch,
        SilentClient(
            device_info_gatt("3220", "T-SUB-3.0.3-master+0"), [atom_service()]
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    with caplog.at_level(logging.DEBUG):
        await data.update_device(ble_device())

    timeouts = [
        record
        for record in caplog.records
        if "Timeout getting command data" in record.message
    ]
    assert timeouts
    assert not [
        record for record in caplog.records if record.levelno >= logging.WARNING
    ]
