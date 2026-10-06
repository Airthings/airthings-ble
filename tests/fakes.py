import asyncio
from typing import Any, Callable
from uuid import UUID

import cbor2
import pytest
from airthings_ble.const import (
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

_ATOM_RESPONSE_HEADER = bytes.fromhex("1001000345")


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
        atom_latest_values: dict[str, Any] | None = None,
        chunk_size: int | None = None,
        extra_notification: bytes | None = None,
        write_error: Exception | None = None,
        stop_notify_error: Exception | None = None,
        stall_write: bool = False,
        stall_stop_notify: bool = False,
        command_response: bytes | None = None,
        read_delay: float = 0,
        read_error: BleakError | None = None,
    ) -> None:
        self.address = ADDRESS
        self.services = services or []
        self._gatt = {str(uuid): value for uuid, value in gatt.items()}
        self._failing = {str(uuid) for uuid in failing or set()}
        self._atom_latest_values = atom_latest_values or ATOM_LATEST_VALUES
        self._chunk_size = chunk_size
        self._extra_notification = extra_notification
        self._write_error = write_error
        self._stop_notify_error = stop_notify_error
        self._stall_write = stall_write
        self._stall_stop_notify = stall_stop_notify
        self._command_response = command_response
        self._read_delay = read_delay
        self._read_error = read_error
        self._callback: Callable[[Any, bytearray], None] | None = None
        self.cache_cleared = False
        self.stop_notify_calls = 0
        self.disconnected = False

    async def read_gatt_char(self, characteristic: Any) -> bytearray:
        uuid = str(getattr(characteristic, "uuid", characteristic))
        if self._read_delay:
            await asyncio.sleep(self._read_delay)
        if uuid in self._failing:
            raise self._read_error or BleakError(f"Failed to read {uuid}")
        return bytearray(self._gatt[uuid])

    async def start_notify(
        self, char_specifier: Any, callback: Callable[[Any, bytearray], None]
    ) -> None:
        if self._callback is not None:
            raise ValueError("Characteristic notifications already started")
        self._callback = callback

    async def stop_notify(self, char_specifier: Any) -> None:
        self.stop_notify_calls += 1
        if self._stall_stop_notify:
            await asyncio.Event().wait()
        if self._stop_notify_error is not None:
            raise self._stop_notify_error
        self._callback = None

    @property
    def notifying(self) -> bool:
        return self._callback is not None

    async def write_gatt_char(self, characteristic: Any, data: bytearray) -> None:
        if self._write_error is not None:
            raise self._write_error
        if self._stall_write:
            await asyncio.Event().wait()
        if self._command_response is not None:
            self._notify(characteristic, self._command_response)
            return
        random_bytes = bytes(data[2:4])
        path = cbor2.loads(bytes(data[7:]))
        if path.endswith("31012"):
            payload: int | bytes = cbor2.dumps(self._atom_latest_values)
        else:
            payload = ATOM_CONNECTIVITY_MODE_BLE
        response = (
            _ATOM_RESPONSE_HEADER + random_bytes + cbor2.dumps([{0: path, 2: payload}])
        )
        self._notify(characteristic, response)

    def _notify(self, characteristic: Any, response: bytes) -> None:
        callback = self._callback
        assert callback is not None
        loop = asyncio.get_running_loop()
        size = self._chunk_size or len(response)
        for start in range(0, len(response), size):
            loop.call_soon(
                callback, characteristic, bytearray(response[start : start + size])
            )
        if self._extra_notification is not None:
            loop.call_soon(
                callback, characteristic, bytearray(self._extra_notification)
            )

    async def disconnect(self) -> None:
        self.disconnected = True

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
        return remaining.pop(0)

    monkeypatch.setattr(
        "airthings_ble.parser.establish_connection", fake_establish_connection
    )


def ble_device(name: str | None = None) -> BLEDevice:
    return BLEDevice(ADDRESS, name, None)
