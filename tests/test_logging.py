import asyncio
import logging
from typing import Any, Callable

import pytest
from airthings_ble import AirthingsBluetoothDeviceData
from airthings_ble.command_decode import NotificationReceiver
from airthings_ble.const import CHAR_UUID_FIRMWARE_REV, COMMAND_UUID_WAVE_PLUS

from fakes import (
    FakeClient,
    FakeService,
    atom_service,
    ble_device,
    device_info_gatt,
    use_clients,
)

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


@pytest.mark.asyncio
@pytest.mark.command_timeout
@pytest.mark.parametrize(
    ("model", "services", "partial_response"),
    [
        ("2930", lambda: [FakeService([COMMAND_UUID_WAVE_PLUS])], "6d00"),
        ("3220", lambda: [atom_service()], "1001000345123481a2"),
    ],
)
async def test_partial_command_response_is_not_decoded(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    model: str,
    services: Callable[[], list[FakeService]],
    partial_response: str,
) -> None:
    """Test a response cut short by the command timeout is dropped without a warning."""
    wait_for_message = NotificationReceiver.wait_for_message

    async def short_wait(self: NotificationReceiver, timeout: float) -> None:
        await wait_for_message(self, 0.01)

    monkeypatch.setattr(NotificationReceiver, "wait_for_message", short_wait)
    use_clients(
        monkeypatch,
        FakeClient(
            device_info_gatt(model, "T-SUB-3.0.3-master+0"),
            services(),
            command_response=bytes.fromhex(partial_response),
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    with caplog.at_level(logging.DEBUG):
        device = await data.update_device(ble_device())

    assert "battery" not in device.sensors
    assert not [
        record for record in caplog.records if record.levelno >= logging.WARNING
    ]


@pytest.mark.asyncio
@pytest.mark.command_timeout
@pytest.mark.parametrize(
    ("model", "services", "command_response"),
    [
        (
            "2930",
            lambda: [FakeService([COMMAND_UUID_WAVE_PLUS])],
            bytes.fromhex(
                "6d00600c04000100008211ff00000000c04c20001f3560007006B80B0900"
            ),
        ),
        ("3220", lambda: [atom_service()], None),
    ],
)
async def test_response_completed_at_the_timeout_is_decoded(
    monkeypatch: pytest.MonkeyPatch,
    model: str,
    services: Callable[[], list[FakeService]],
    command_response: bytes | None,
) -> None:
    """Test a response that completes as the command times out is still used."""

    async def complete_then_time_out(
        self: NotificationReceiver, timeout: float
    ) -> None:
        await asyncio.sleep(0.05)
        raise asyncio.TimeoutError

    monkeypatch.setattr(
        NotificationReceiver, "wait_for_message", complete_then_time_out
    )
    use_clients(
        monkeypatch,
        FakeClient(
            device_info_gatt(model, "T-SUB-3.0.3-master+0"),
            services(),
            command_response=command_response,
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert "battery" in device.sensors
