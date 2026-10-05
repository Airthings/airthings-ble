import logging
from typing import Any, Callable
from uuid import UUID

import cbor2
import pytest
from airthings_ble import AirthingsBluetoothDeviceData
from airthings_ble.const import (
    CHAR_UUID_FIRMWARE_REV,
    CHAR_UUID_MODEL_NUMBER_STRING,
    COMMAND_UUID_ATOM,
    COMMAND_UUID_ATOM_NOTIFY,
)
from bleak.backends.device import BLEDevice

_LOGGER = logging.getLogger(__name__)

_ADDRESS = "AA:BB:CC:DD:EE:FF"
_RESPONSE_HEADER = bytes.fromhex("1001000345")
_LATEST_VALUES = {"TMP": 29424, "HUM": 3375, "BAT": 2868, "TIM": 118}
_CONNECTIVITY_MODE_BLE = 4


class FakeCharacteristic:
    def __init__(self, uuid: UUID) -> None:
        self.uuid = str(uuid)


class FakeAtomService:
    def __init__(self) -> None:
        self.characteristics = [
            FakeCharacteristic(COMMAND_UUID_ATOM),
            FakeCharacteristic(COMMAND_UUID_ATOM_NOTIFY),
        ]

    def get_characteristic(self, uuid: UUID) -> FakeCharacteristic | None:
        return next((c for c in self.characteristics if c.uuid == str(uuid)), None)


class FakeClient:
    """Answers GATT reads from a table and Atom requests with a canned response."""

    def __init__(self, gatt: dict[UUID, bytes], atom: bool) -> None:
        self.address = _ADDRESS
        self.services = [FakeAtomService()] if atom else []
        self._gatt = {str(uuid): value for uuid, value in gatt.items()}
        self._callback: Callable[[Any, bytearray], None] | None = None

    async def read_gatt_char(self, characteristic: Any) -> bytearray:
        return bytearray(
            self._gatt[str(getattr(characteristic, "uuid", characteristic))]
        )

    async def start_notify(
        self, char_specifier: Any, callback: Callable[[Any, bytearray], None]
    ) -> None:
        self._callback = callback

    async def stop_notify(self, char_specifier: Any) -> None:
        self._callback = None

    async def write_gatt_char(self, characteristic: Any, data: bytearray) -> None:
        random_bytes = bytes(data[2:4])
        path = cbor2.loads(bytes(data[7:]))
        if path.endswith("31012"):
            payload: int | bytes = cbor2.dumps(_LATEST_VALUES)
        else:
            payload = _CONNECTIVITY_MODE_BLE
        response = (
            _RESPONSE_HEADER + random_bytes + cbor2.dumps([{0: path, 2: payload}])
        )
        assert self._callback is not None
        self._callback(characteristic, bytearray(response))

    async def disconnect(self) -> None:
        pass

    async def clear_cache(self) -> None:
        pass


def _gatt(model: str, firmware: str) -> dict[UUID, bytes]:
    return {
        CHAR_UUID_MODEL_NUMBER_STRING: model.encode(),
        CHAR_UUID_FIRMWARE_REV: firmware.encode(),
        UUID("00002a29-0000-1000-8000-00805f9b34fb"): b"Airthings AS",
        UUID("00002a27-0000-1000-8000-00805f9b34fb"): b"REV A",
        UUID("00002a00-0000-1000-8000-00805f9b34fb"): b"Airthings device",
        UUID("00002a25-0000-1000-8000-00805f9b34fb"): b"123456",
    }


async def _poll(
    monkeypatch: pytest.MonkeyPatch,
    data: AirthingsBluetoothDeviceData,
    client: FakeClient,
) -> Any:
    async def fake_establish_connection(*args: Any, **kwargs: Any) -> FakeClient:
        return client

    monkeypatch.setattr(
        "airthings_ble.parser.establish_connection", fake_establish_connection
    )
    return await data.update_device(BLEDevice(_ADDRESS, None, None))


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

    before = await _poll(
        monkeypatch, data, FakeClient(_gatt(model, old_firmware), atom=True)
    )
    assert before.sw_version == old_firmware
    assert before.firmware.current_version == old_version
    assert before.firmware.need_firmware_upgrade is True
    assert before.sensors["battery"] is not None

    after = await _poll(
        monkeypatch,
        data,
        FakeClient({CHAR_UUID_FIRMWARE_REV: new_firmware.encode()}, atom=True),
    )
    assert after.sw_version == new_firmware
    assert after.firmware.current_version == new_version
    assert after.firmware.need_firmware_upgrade is False


@pytest.mark.asyncio
async def test_wave_plus_firmware_refreshes_between_polls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test the Wave Plus firmware string follows the device across polls."""
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    before = await _poll(
        monkeypatch,
        data,
        FakeClient(_gatt("2930", "G-BLE-1.5.3-master+0"), atom=False),
    )
    assert before.sw_version == "G-BLE-1.5.3-master+0"

    after = await _poll(
        monkeypatch,
        data,
        FakeClient({CHAR_UUID_FIRMWARE_REV: b"G-BLE-2.2.3-master+0"}, atom=False),
    )
    assert after.sw_version == "G-BLE-2.2.3-master+0"
    assert data.device_info.sw_version == "G-BLE-2.2.3-master+0"
