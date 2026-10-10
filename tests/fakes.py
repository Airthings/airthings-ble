import asyncio
from typing import Any, Callable
from uuid import UUID

import cbor2
import pytest
from airthings_ble.atom.request_path import AtomRequestPath
from airthings_ble.const import (
    ATOM_RESPONSE_HEADER,
    CHAR_UUID_FIRMWARE_REV,
    CHAR_UUID_MODEL_NUMBER_STRING,
    COMMAND_UUID_ATOM,
    COMMAND_UUID_ATOM_NOTIFY,
)
from bleak import BleakError
from bleak.backends.device import BLEDevice

ADDRESS = "AA:BB:CC:DD:EE:FF"
ATOM_LATEST_VALUES = {"TMP": 29424, "HUM": 3375, "BAT": 2868, "TIM": 118}
ATOM_CONNECTIVITY_MODE_BLE = 4
SUB_CHIP_VERSION_REQUEST = bytes.fromhex("720100000000000000")
SUB_CHIP_VERSION_RESPONSE = bytes.fromhex("720002050100")

CALLBACK_ERRORS: list[BaseException] = []


def _recording_errors(
    callback: Callable[[Any, bytearray], None],
) -> Callable[[Any, bytearray], None]:
    def wrapper(sender: Any, data: bytearray) -> None:
        try:
            callback(sender, data)
        except Exception as err:  # noqa: BLE001
            CALLBACK_ERRORS.append(err)
            raise

    return wrapper


_NOTIFICATION_INTERVAL = 0.001


def atom_fragments(response: bytes, size: int | None = None) -> list[bytes]:
    """Split an Atom response into notifications of at most size bytes."""
    step = (size or len(response) + 3) - 3
    parts = [response[start : start + step] for start in range(0, len(response), step)]
    return [b"\x10" + len(parts).to_bytes(2, "little") + parts[0]] + [
        b"\x00" + position.to_bytes(2, "little") + part
        for position, part in enumerate(parts[1:], start=2)
    ]


class FakeCharacteristic:
    def __init__(self, uuid: UUID | str) -> None:
        self.uuid = str(uuid)


class FakeService:
    def __init__(self, uuids: list[UUID | str]) -> None:
        self.characteristics = [FakeCharacteristic(uuid) for uuid in uuids]

    def get_characteristic(self, uuid: UUID | str) -> FakeCharacteristic | None:
        return next((c for c in self.characteristics if c.uuid == str(uuid)), None)


def atom_service() -> FakeService:
    return FakeService([COMMAND_UUID_ATOM, COMMAND_UUID_ATOM_NOTIFY])


class FakeClient:
    """Answers GATT reads from a table and Atom requests with a canned response."""

    def __init__(
        self,
        gatt: dict[UUID, bytes],
        services: list[FakeService] | None = None,
        failing: set[UUID] | None = None,
        atom_latest_values: Any = None,
        atom_connectivity_mode: Any = None,
        chunk_size: int | None = None,
        extra_notification: bytes | None = None,
        write_error: Exception | None = None,
        stop_notify_error: Exception | None = None,
        stall_write: bool = False,
        stall_stop_notify: bool = False,
        command_response: bytes | None = None,
        read_delay: float = 0,
        silent_commands: bool = False,
        read_error: BleakError | None = None,
        disconnect_on_read: UUID | None = None,
        sub_chip_version_response: bytes | None = SUB_CHIP_VERSION_RESPONSE,
        sub_chip_version_error: Exception | None = None,
    ) -> None:
        self.address = ADDRESS
        self.services = services or []
        self._gatt = {str(uuid): value for uuid, value in gatt.items()}
        self._failing = {str(uuid) for uuid in failing or set()}
        self._atom_latest_values = (
            ATOM_LATEST_VALUES if atom_latest_values is None else atom_latest_values
        )
        self._chunk_size = chunk_size
        self._extra_notification = extra_notification
        self._write_error = write_error
        self._stop_notify_error = stop_notify_error
        self._stall_write = stall_write
        self._stall_stop_notify = stall_stop_notify
        self._command_response = command_response
        self._read_delay = read_delay
        self._atom_connectivity_mode = (
            ATOM_CONNECTIVITY_MODE_BLE
            if atom_connectivity_mode is None
            else atom_connectivity_mode
        )
        self._silent_commands = silent_commands
        self._sub_chip_version_response = sub_chip_version_response
        self._sub_chip_version_error = sub_chip_version_error
        self._read_error = read_error
        self._disconnect_on_read = (
            None if disconnect_on_read is None else str(disconnect_on_read)
        )
        self.disconnected_callback: Callable[[Any], None] | None = None
        self.cache_cleared = False
        self.reads: list[str] = []
        self.notifications: list[bytes] = []
        self.writes: list[bytes] = []
        self._callback: Callable[[Any, bytearray], None] | None = None
        self._notify_uuid: str | None = None
        self.stop_notify_calls = 0
        self.disconnected = False

    async def read_gatt_char(self, characteristic: Any) -> bytearray:
        uuid = str(getattr(characteristic, "uuid", characteristic))
        self.reads.append(uuid)
        if self._read_delay:
            await asyncio.sleep(self._read_delay)
        if uuid == self._disconnect_on_read:
            assert self.disconnected_callback is not None
            self.disconnected_callback(self)
            await asyncio.Event().wait()
        if uuid in self._failing:
            raise self._read_error or BleakError(f"Failed to read {uuid}")
        return bytearray(self._gatt[uuid])

    async def start_notify(
        self, char_specifier: Any, callback: Callable[[Any, bytearray], None]
    ) -> None:
        if self._callback is not None:
            raise ValueError("Characteristic notifications already started")
        notify_uuid = str(getattr(char_specifier, "uuid", char_specifier))
        self._assert_in_services(notify_uuid)
        self._notify_uuid = notify_uuid
        self._callback = callback

    def _assert_in_services(self, uuid: str) -> None:
        known = {c.uuid for service in self.services for c in service.characteristics}
        assert uuid in known, f"{uuid} is not in the device's services"

    async def stop_notify(self, char_specifier: Any) -> None:
        self.stop_notify_calls += 1
        stop_uuid = str(getattr(char_specifier, "uuid", char_specifier))
        assert (
            stop_uuid == self._notify_uuid
        ), f"stopped {stop_uuid} while notifying on {self._notify_uuid}"
        if self._stall_stop_notify:
            await asyncio.Event().wait()
        if self._stop_notify_error is not None:
            raise self._stop_notify_error
        self._callback = None

    @property
    def notifying(self) -> bool:
        return self._callback is not None

    async def write_gatt_char(self, characteristic: Any, data: bytearray) -> None:
        write_uuid = str(getattr(characteristic, "uuid", characteristic))
        self._assert_in_services(write_uuid)
        expected_notify_uuid = (
            str(COMMAND_UUID_ATOM_NOTIFY)
            if write_uuid == str(COMMAND_UUID_ATOM)
            else write_uuid
        )
        assert (
            self._notify_uuid == expected_notify_uuid
        ), f"wrote {write_uuid} while notifying on {self._notify_uuid}"
        self.writes.append(bytes(data))
        if self._write_error is not None:
            raise self._write_error
        if self._stall_write:
            await asyncio.Event().wait()
        if write_uuid == str(COMMAND_UUID_ATOM):
            assert (
                data[0:2] == b"\x03\x01" and data[4:7] == b"\x81\xa1\x00"
            ), f"malformed Atom request {data.hex()}"
        elif data == SUB_CHIP_VERSION_REQUEST:
            if self._sub_chip_version_error is not None:
                raise self._sub_chip_version_error
            if self._sub_chip_version_response is not None:
                self._notify(characteristic, self._sub_chip_version_response)
            return
        else:
            assert data == b"\x6d", f"malformed Wave command {data.hex()}"
        if self._silent_commands:
            return
        if self._command_response is not None:
            self._notify(characteristic, self._command_response)
            return
        random_bytes = bytes(data[2:4])
        path = cbor2.loads(bytes(data[7:]))
        if path == AtomRequestPath.LATEST_VALUES:
            payload: int | bytes = cbor2.dumps(self._atom_latest_values)
        else:
            assert (
                path == AtomRequestPath.CONNECTIVITY_MODE
            ), f"unknown Atom path {path}"
            payload = self._atom_connectivity_mode
        response = (
            ATOM_RESPONSE_HEADER + random_bytes + cbor2.dumps([{0: path, 2: payload}])
        )
        self._send(characteristic, atom_fragments(response, self._chunk_size))

    def _notify(self, characteristic: Any, response: bytes) -> None:
        size = self._chunk_size or len(response)
        self._send(
            characteristic,
            [response[start : start + size] for start in range(0, len(response), size)],
        )

    def _send(self, characteristic: Any, chunks: list[bytes]) -> None:
        assert self._callback is not None
        loop = asyncio.get_running_loop()
        callback = _recording_errors(self._callback)
        start_time = loop.time()
        for index, chunk in enumerate(chunks):
            loop.call_at(
                start_time + index * _NOTIFICATION_INTERVAL,
                self._deliver,
                callback,
                characteristic,
                chunk,
            )
        if self._extra_notification is not None:
            loop.call_at(
                start_time + (len(chunks) - 1) * _NOTIFICATION_INTERVAL,
                self._deliver,
                callback,
                characteristic,
                self._extra_notification,
            )

    def _deliver(
        self,
        callback: Callable[[Any, bytearray], None],
        characteristic: Any,
        data: bytes,
    ) -> None:
        self.notifications.append(data)
        callback(characteristic, bytearray(data))

    async def disconnect(self) -> None:
        self.disconnected = True
        if self.disconnected_callback is not None:
            self.disconnected_callback(self)

    async def clear_cache(self) -> None:
        self.cache_cleared = True


def device_info_gatt(model: str, firmware: str) -> dict[UUID, bytes]:
    return {
        CHAR_UUID_MODEL_NUMBER_STRING: model.encode(),
        CHAR_UUID_FIRMWARE_REV: firmware.encode(),
        UUID("00002a29-0000-1000-8000-00805f9b34fb"): b"Airthings AS",
        UUID("00002a27-0000-1000-8000-00805f9b34fb"): b"REV A",
        UUID("00002a00-0000-1000-8000-00805f9b34fb"): b"Airthings device",
        UUID("00002a25-0000-1000-8000-00805f9b34fb"): b"123456",
    }


def use_clients(monkeypatch: pytest.MonkeyPatch, *clients: FakeClient) -> None:
    """Make each connection attempt return the next client in order."""
    remaining = list(clients)

    async def fake_establish_connection(*args: Any, **kwargs: Any) -> FakeClient:
        client = remaining.pop(0)
        client.disconnected_callback = kwargs["disconnected_callback"]
        return client

    monkeypatch.setattr(
        "airthings_ble.parser.establish_connection", fake_establish_connection
    )


def ble_device(name: str | None = None) -> BLEDevice:
    return BLEDevice(ADDRESS, name, None)
