import asyncio
import logging
from uuid import UUID

import pytest
from airthings_ble import AirthingsBluetoothDeviceData
from airthings_ble.command_decode import AtomNotificationReceiver, NotificationReceiver
from airthings_ble.const import COMMAND_UUID_WAVE_MINI, COMMAND_UUID_WAVE_PLUS

from fakes import (
    FakeClient,
    FakeService,
    atom_service,
    ble_device,
    device_info_gatt,
    use_clients,
)

_LOGGER = logging.getLogger(__name__)

_WAVE_ENHANCE_LATEST_VALUES = {
    "NOI": 39,
    "TMP": 29424,
    "HUM": 3375,
    "CO2": 732,
    "VOC": 277,
    "LUX": 1,
    "PRS": 6239814,
    "BAT": 2868,
    "TIM": 118,
}


@pytest.mark.asyncio
async def test_atom_response_split_over_notifications(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test an Atom response delivered in 20-byte chunks is reassembled."""
    use_clients(
        monkeypatch,
        FakeClient(
            device_info_gatt("3220", "T-SUB-3.0.3-master+0"),
            [atom_service()],
            atom_latest_values=_WAVE_ENHANCE_LATEST_VALUES,
            chunk_size=20,
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert device.sensors == {
        "connectivity_mode": "Bluetooth",
        "battery": device.model.battery_percentage(2.868),
        "lux": 1,
        "co2": 732,
        "voc": 277,
        "humidity": 33.75,
        "temperature": 21.09,
        "noise": 39,
        "pressure": 974.9709375,
    }


@pytest.mark.asyncio
async def test_atom_notification_after_complete_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a stray notification after a complete Atom response is ignored."""
    use_clients(
        monkeypatch,
        FakeClient(
            device_info_gatt("3220", "T-SUB-3.0.3-master+0"),
            [atom_service()],
            extra_notification=b"\x00" * 20,
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert device.sensors["temperature"] == 21.09


@pytest.mark.asyncio
async def test_notification_after_complete_message() -> None:
    """Test a notification after the message is complete does not raise."""
    receiver = NotificationReceiver(4)
    receiver(None, bytearray(b"\x01\x02\x03\x04"))
    receiver(None, bytearray(b"\x05"))

    await receiver.wait_for_message(1)
    assert receiver.message == bytearray(b"\x01\x02\x03\x04")


@pytest.mark.asyncio
async def test_notification_after_timeout() -> None:
    """Test a notification arriving after the timeout does not raise."""
    receiver = NotificationReceiver(4)

    with pytest.raises(asyncio.TimeoutError):
        await receiver.wait_for_message(0.01)

    receiver(None, bytearray(b"\x01\x02\x03\x04"))


@pytest.mark.asyncio
async def test_atom_receiver_waits_for_complete_cbor() -> None:
    """Test the Atom receiver is incomplete until its CBOR payload is."""
    receiver = AtomNotificationReceiver()
    receiver(None, bytearray.fromhex("10010003451234"))
    receiver(None, bytearray.fromhex("81a2"))

    with pytest.raises(asyncio.TimeoutError):
        await receiver.wait_for_message(0.01)

    receiver(None, bytearray.fromhex("00010203"))
    assert receiver.message == bytearray.fromhex("1001000345123481a200010203")


@pytest.mark.asyncio
async def test_atom_receiver_completes_on_invalid_cbor() -> None:
    """Test the Atom receiver hands invalid CBOR over to be rejected by parsing."""
    receiver = AtomNotificationReceiver()
    receiver(None, bytearray.fromhex("1001000345123481a2ff"))

    await receiver.wait_for_message(1)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("model", "command_uuid", "response", "first_chunk_size"),
    [
        (
            "2930",
            COMMAND_UUID_WAVE_PLUS,
            "6d00600c04000100008211ff00000000c04c20001f3560007006B80B0900",
            28,
        ),
        (
            "2920",
            COMMAND_UUID_WAVE_MINI,
            "6d0064000000c800000001020304f4015802bc02000020038403b80b4c04b0040000",
            32,
        ),
    ],
)
async def test_wave_command_response_waits_for_header_bytes(
    monkeypatch: pytest.MonkeyPatch,
    model: str,
    command_uuid: UUID,
    response: str,
    first_chunk_size: int,
) -> None:
    """Test a Wave command response is not complete before its last two bytes."""
    use_clients(
        monkeypatch,
        FakeClient(
            device_info_gatt(model, "G-BLE-1.5.3-master+0"),
            [FakeService([command_uuid])],
            command_response=bytes.fromhex(response),
            chunk_size=first_chunk_size,
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert device.sensors == {"battery": device.model.battery_percentage(3.0)}


@pytest.mark.asyncio
async def test_message_completing_as_the_timeout_fires() -> None:
    """Test a message completed in the same loop pass as the timeout is kept."""
    loop = asyncio.get_running_loop()
    errors: list[dict[str, object]] = []
    loop.set_exception_handler(lambda _, context: errors.append(context))
    receiver = NotificationReceiver(4)
    loop.call_soon(receiver, None, bytearray(b"\x01\x02\x03\x04"))

    await receiver.wait_for_message(0)

    assert receiver.message == bytearray(b"\x01\x02\x03\x04")
    assert errors == []
