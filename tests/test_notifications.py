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
    client = FakeClient(
        device_info_gatt("3220", "T-SUB-3.0.3-master+0"),
        [atom_service()],
        extra_notification=b"\x00" * 20,
    )
    use_clients(monkeypatch, client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert device.sensors["temperature"] == 21.09
    assert client.notifications.count(b"\x00" * 20) == 2


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
@pytest.mark.parametrize(
    ("fragments", "expected"),
    [
        (["100100aabbcc"], "aabbcc"),
        (["100300aa", "000200bb", "000300cc"], "aabbcc"),
        (["100300aa", "000300cc", "000200bb"], "aabbcc"),
        (["000300cc", "100300aa", "000200bb"], "aabbcc"),
        (["300200aa", "200200bb"], "aabb"),
        (["400200dd", "100200aa", "000200bb"], "aabb"),
        (["100200aa", "000100dd", "000200bb"], "aabb"),
        (["100200aa", "300100dd", "000200bb"], "aabb"),
    ],
)
async def test_atom_receiver_reassembles_fragments(
    fragments: list[str], expected: str
) -> None:
    """Test the Atom receiver joins the fragments of one response in order."""
    receiver = AtomNotificationReceiver()
    for fragment in fragments:
        receiver(None, bytearray.fromhex(fragment))

    await receiver.wait_for_message(1)
    assert receiver.message == bytearray.fromhex(expected)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fragments",
    [
        ["100300aa", "000200bb"],
        ["000200bb", "000300cc"],
        ["100000aa"],
        [""],
        ["10"],
        ["1003"],
        ["110100aa"],
        ["100200aa", "200200bb"],
        ["100200aa", "000100bb"],
        ["100002aa", "000200bb"],
    ],
)
async def test_atom_receiver_waits_for_every_fragment(fragments: list[str]) -> None:
    """Test the Atom receiver ignores invalid fragments and waits for missing ones."""
    receiver = AtomNotificationReceiver()
    for fragment in fragments:
        receiver(None, bytearray.fromhex(fragment))

    with pytest.raises(asyncio.TimeoutError):
        await receiver.wait_for_message(0.01)
    assert not receiver.complete


@pytest.mark.asyncio
async def test_atom_receiver_completes_after_timeout() -> None:
    """Test an Atom response that completes after the wait timed out is kept."""
    receiver = AtomNotificationReceiver()
    receiver(None, bytearray.fromhex("100200aa"))
    with pytest.raises(asyncio.TimeoutError):
        await receiver.wait_for_message(0.01)

    receiver(None, bytearray.fromhex("000200bb"))

    assert receiver.complete
    assert receiver.message == bytearray.fromhex("aabb")


@pytest.mark.asyncio
async def test_atom_receiver_ignores_fragments_after_completion() -> None:
    """Test a late fragment does not change a reassembled Atom response."""
    receiver = AtomNotificationReceiver()
    receiver(None, bytearray.fromhex("100100aa"))
    receiver(None, bytearray.fromhex("100100bb"))

    await receiver.wait_for_message(1)
    assert receiver.message == bytearray.fromhex("aa")


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
