import logging
from typing import Any, Callable
from uuid import UUID

import pytest
from airthings_ble import (
    AirthingsBluetoothDeviceData,
    AirthingsChip,
    AirthingsDevice,
    AirthingsDeviceType,
)
from airthings_ble.command_decode import COMMAND_DECODERS, CommandDecode
from airthings_ble.const import (
    BATTERY,
    CHAR_UUID_DATETIME,
    CHAR_UUID_FIRMWARE_REV,
    CHAR_UUID_HARDWARE_REV,
    CHAR_UUID_HUMIDITY,
    CHAR_UUID_ILLUMINANCE_ACCELEROMETER,
    CHAR_UUID_RADON_1DAYAVG,
    CHAR_UUID_RADON_LONG_TERM_AVG,
    CHAR_UUID_TEMPERATURE,
    CHAR_UUID_WAVE_2_DATA,
    CHAR_UUID_WAVE_PLUS_DATA,
    CHAR_UUID_WAVEMINI_DATA,
    COMMAND_UUID_WAVE_2,
    COMMAND_UUID_WAVE_MINI,
    COMMAND_UUID_WAVE_PLUS,
    SUB_CHIP_VERSION_MAX_AGE,
)

from bleak import BleakError

from fakes import (
    SUB_CHIP_VERSION_REQUEST,
    FakeClient,
    FakeService,
    ble_device,
    device_info_gatt,
    use_clients,
)

_LOGGER = logging.getLogger(__name__)

_WAVE_PLUS_DATA = "01380d800b002200bd094cc31d036c0000007d05"
_WAVE_RADON_DATA = "013860f009001100a709ffffffffffff0000ffff"
_WAVE_MINI_DATA = "1800327431c168102e000000ff940700ffffffff"
_WAVE_PLUS_COMMAND = "6d00600c04000100008211ff00000000c04c20001f3560007006B80B0900"
_WAVE_MINI_COMMAND = (
    "6d0064000000c800000001020304f4015802bc02000020038403b80b4c04b0040000"
)
_SELF_CHECK_REQUEST = b"\x6d"
_WAVE_PLUS_CHIP_VERSIONS = {
    AirthingsChip.BLE: "1.5.3",
    AirthingsChip.MSP: "2.2.0",
    AirthingsChip.SUB: "2.5.1",
}
_UNRELATED_CHARACTERISTIC = UUID("b42e0000-ade7-11e4-89d3-123b93f75cba")


def _wave_client(
    model: str,
    data_uuid: UUID,
    data: str,
    command_uuid: UUID,
    command: str,
    firmware: str = "G-BLE-1.5.3-master+0",
    client_class: type[FakeClient] = FakeClient,
    **kwargs: Any,
) -> FakeClient:
    gatt = device_info_gatt(model, firmware)
    gatt[data_uuid] = bytes.fromhex(data)
    return client_class(
        gatt,
        [FakeService([data_uuid, command_uuid])],
        command_response=bytes.fromhex(command),
        **kwargs,
    )


@pytest.mark.asyncio
async def test_wave_plus_update(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test a Wave Plus reports its sensor data and battery from the command."""
    use_clients(
        monkeypatch,
        _wave_client(
            "2930",
            CHAR_UUID_WAVE_PLUS_DATA,
            _WAVE_PLUS_DATA,
            COMMAND_UUID_WAVE_PLUS,
            _WAVE_PLUS_COMMAND,
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert device.model == AirthingsDeviceType.WAVE_PLUS
    assert device.sensors == {
        "humidity": 28.0,
        "illuminance": 5,
        "radon_1day_avg": 11,
        "radon_1day_level": "good",
        "radon_longterm_avg": 34,
        "radon_longterm_level": "good",
        "temperature": 24.93,
        "pressure": 999.92,
        "co2": 797.0,
        "voc": 108.0,
        "battery": 100,
    }
    assert device.sw_version == "G-BLE-1.5.3-master+0"
    assert device.chip_versions == _WAVE_PLUS_CHIP_VERSIONS


@pytest.mark.asyncio
async def test_wave_radon_update(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test a Wave Radon reports its sensor data and battery from the command."""
    use_clients(
        monkeypatch,
        _wave_client(
            "2950",
            CHAR_UUID_WAVE_2_DATA,
            _WAVE_RADON_DATA,
            COMMAND_UUID_WAVE_2,
            _WAVE_PLUS_COMMAND,
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert device.model == AirthingsDeviceType.WAVE_RADON
    assert device.sensors == {
        "illuminance": 37,
        "humidity": 28.0,
        "radon_1day_avg": 9,
        "radon_1day_level": "good",
        "radon_longterm_avg": 17,
        "radon_longterm_level": "good",
        "temperature": 24.71,
        "battery": 100,
    }
    assert device.chip_versions == _WAVE_PLUS_CHIP_VERSIONS


@pytest.mark.asyncio
async def test_wave_mini_update(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test a Wave Mini reports its sensor data and three-battery percentage."""
    use_clients(
        monkeypatch,
        _wave_client(
            "2920",
            CHAR_UUID_WAVEMINI_DATA,
            _WAVE_MINI_DATA,
            COMMAND_UUID_WAVE_MINI,
            _WAVE_MINI_COMMAND,
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert device.model == AirthingsDeviceType.WAVE_MINI
    assert device.sensors == {
        "illuminance": 9,
        "temperature": 24.31,
        "pressure": 989.14,
        "humidity": 42.0,
        "voc": 46.0,
        "battery": 15,
    }
    assert device.chip_versions == {
        AirthingsChip.BLE: "1.5.3",
        AirthingsChip.SUB: "0.0.2",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("firmware", "ble_version"),
    [
        pytest.param("M-BLE-2.4.0-master+0", "2.4.0", id="from_firmware_revision"),
        pytest.param("2.4.9", "2.4.9", id="from_self_check"),
        pytest.param("M-BLE-999.2.3", "2.4.9", id="invalid_revision"),
    ],
)
async def test_wave_mini_chip_versions(
    monkeypatch: pytest.MonkeyPatch, firmware: str, ble_version: str
) -> None:
    """Test a Wave Mini reports its BLE and SUB versions."""
    use_clients(
        monkeypatch,
        _wave_client(
            "2920",
            CHAR_UUID_WAVEMINI_DATA,
            _WAVE_MINI_DATA,
            COMMAND_UUID_WAVE_MINI,
            "6d00640000000709040201020304"
            "f401580200020202"
            "20038403b80b4cc4b0040000",
            firmware=firmware,
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert device.sw_version == firmware
    assert device.chip_versions == {
        AirthingsChip.BLE: ble_version,
        AirthingsChip.SUB: "2.2.2",
    }


@pytest.mark.asyncio
async def test_wave_radon_in_pci(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test Wave radon is converted to pCi/L while its level stays Bq/m3 based."""
    use_clients(
        monkeypatch,
        _wave_client(
            "2930",
            CHAR_UUID_WAVE_PLUS_DATA,
            "01380d80a0000001bd094cc31d036c0000007d05",
            COMMAND_UUID_WAVE_PLUS,
            _WAVE_PLUS_COMMAND,
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER, is_metric=False)

    device = await data.update_device(ble_device())

    assert device.sensors["radon_1day_avg"] == pytest.approx(160 * 0.027)
    assert device.sensors["radon_1day_level"] == "poor"
    assert device.sensors["radon_longterm_avg"] == pytest.approx(256 * 0.027)
    assert device.sensors["radon_longterm_level"] == "poor"


def _wave_gen_1_gatt() -> dict[UUID, bytes]:
    gatt = device_info_gatt("2900", "1.0.0")
    gatt[CHAR_UUID_DATETIME] = bytes.fromhex("e8070a060c1e00")
    gatt[CHAR_UUID_TEMPERATURE] = bytes.fromhex("0cfe")
    gatt[CHAR_UUID_HUMIDITY] = bytes.fromhex("c611")
    gatt[CHAR_UUID_RADON_1DAYAVG] = bytes.fromhex("7800")
    gatt[CHAR_UUID_RADON_LONG_TERM_AVG] = bytes.fromhex("2200")
    gatt[CHAR_UUID_ILLUMINANCE_ACCELEROMETER] = bytes.fromhex("b20c")
    return gatt


_WAVE_GEN_1_SENSOR_UUIDS = [
    CHAR_UUID_DATETIME,
    CHAR_UUID_TEMPERATURE,
    CHAR_UUID_HUMIDITY,
    CHAR_UUID_RADON_1DAYAVG,
    CHAR_UUID_RADON_LONG_TERM_AVG,
    CHAR_UUID_ILLUMINANCE_ACCELEROMETER,
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("is_metric", "radon_1day", "radon_longterm"),
    [(True, 120, 34), (False, 120 * 0.027, 34 * 0.027)],
)
async def test_wave_gen_1_update(
    monkeypatch: pytest.MonkeyPatch,
    is_metric: bool,
    radon_1day: float,
    radon_longterm: float,
) -> None:
    """Test a Wave Gen 1 reads one characteristic per sensor and drops the clock."""
    client = FakeClient(_wave_gen_1_gatt(), [FakeService(_WAVE_GEN_1_SENSOR_UUIDS)])
    use_clients(monkeypatch, client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER, is_metric=is_metric)

    device = await data.update_device(ble_device())

    assert device.model == AirthingsDeviceType.WAVE_GEN_1
    assert device.hw_version == ""
    assert str(CHAR_UUID_HARDWARE_REV) not in client.reads
    assert device.sensors == {
        "temperature": -5.0,
        "humidity": 45.5,
        "radon_1day_avg": pytest.approx(radon_1day),
        "radon_1day_level": "fair",
        "radon_longterm_avg": pytest.approx(radon_longterm),
        "radon_longterm_level": "good",
        "illuminance": 69,
        "accelerometer": "12.0",
    }
    assert device.chip_versions == {}


@pytest.mark.asyncio
async def test_failed_sensor_read_is_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test a sensor characteristic that fails to read leaves the others intact."""
    use_clients(
        monkeypatch,
        FakeClient(
            _wave_gen_1_gatt(),
            [FakeService(_WAVE_GEN_1_SENSOR_UUIDS)],
            failing={CHAR_UUID_TEMPERATURE},
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert "temperature" not in device.sensors
    assert device.sensors["humidity"] == 45.5


@pytest.mark.asyncio
async def test_unrelated_characteristic_is_not_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a characteristic that is not a known sensor is ignored."""
    gatt = device_info_gatt("2930", "G-BLE-1.5.3-master+0")
    gatt[CHAR_UUID_WAVE_PLUS_DATA] = bytes.fromhex(_WAVE_PLUS_DATA)
    client = FakeClient(
        gatt, [FakeService([_UNRELATED_CHARACTERISTIC, CHAR_UUID_WAVE_PLUS_DATA])]
    )
    use_clients(monkeypatch, client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert str(_UNRELATED_CHARACTERISTIC) not in client.reads
    assert device.sensors["co2"] == 797.0


@pytest.mark.asyncio
@pytest.mark.command_timeout
async def test_wave_command_timeout_keeps_sensor_data(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Test an unanswered self-check gives no battery but keeps sensor data."""
    monkeypatch.setattr("airthings_ble.parser.COMMAND_TIMEOUT", 0.01)
    client = _wave_client(
        "2930",
        CHAR_UUID_WAVE_PLUS_DATA,
        _WAVE_PLUS_DATA,
        COMMAND_UUID_WAVE_PLUS,
        _WAVE_PLUS_COMMAND,
        silent_commands=True,
    )
    use_clients(monkeypatch, client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert "Timeout getting command data" in caplog.text
    assert "battery" not in device.sensors
    assert device.chip_versions == {AirthingsChip.BLE: "1.5.3"}
    assert client.writes == [_SELF_CHECK_REQUEST]
    assert device.sensors["co2"] == 797.0
    assert not client.notifying


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("command", "silent"),
    [
        pytest.param(
            _WAVE_PLUS_COMMAND,
            True,
            id="timeout",
            marks=pytest.mark.command_timeout,
        ),
        pytest.param("6e" + _WAVE_PLUS_COMMAND[2:], False, id="rejected_response"),
    ],
)
async def test_failed_self_check_keeps_chip_versions(
    monkeypatch: pytest.MonkeyPatch, command: str, silent: bool
) -> None:
    """Test chip versions from an earlier self-check survive a failed one."""
    monkeypatch.setattr("airthings_ble.parser.COMMAND_TIMEOUT", 0.01)
    use_clients(
        monkeypatch,
        _wave_client(
            "2930",
            CHAR_UUID_WAVE_PLUS_DATA,
            _WAVE_PLUS_DATA,
            COMMAND_UUID_WAVE_PLUS,
            _WAVE_PLUS_COMMAND,
        ),
        _wave_client(
            "2930",
            CHAR_UUID_WAVE_PLUS_DATA,
            _WAVE_PLUS_DATA,
            COMMAND_UUID_WAVE_PLUS,
            command,
            silent_commands=silent,
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    first = await data.update_device(ble_device())
    second = await data.update_device(ble_device())

    assert first.chip_versions == _WAVE_PLUS_CHIP_VERSIONS
    assert "battery" not in second.sensors
    assert second.chip_versions == _WAVE_PLUS_CHIP_VERSIONS


def _wave_mini_self_check(ble_version: str, sub_version: str) -> str:
    return (
        f"6d0064000000{ble_version}01020304f4015802{sub_version}"
        "20038403b80b4cc4b0040000"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("command", "silent"),
    [
        pytest.param(
            _wave_mini_self_check("07090402", "00020202"),
            True,
            id="timeout",
            marks=pytest.mark.command_timeout,
        ),
        pytest.param(
            "6e" + _wave_mini_self_check("07090402", "00020202")[2:],
            False,
            id="rejected_response",
        ),
    ],
)
async def test_wave_mini_failed_self_check_keeps_cached_versions(
    monkeypatch: pytest.MonkeyPatch, command: str, silent: bool
) -> None:
    """Test a Wave Mini keeps its self-check BLE and SUB versions after a failure."""
    monkeypatch.setattr("airthings_ble.parser.COMMAND_TIMEOUT", 0.01)
    use_clients(
        monkeypatch,
        _wave_client(
            "2920",
            CHAR_UUID_WAVEMINI_DATA,
            _WAVE_MINI_DATA,
            COMMAND_UUID_WAVE_MINI,
            _wave_mini_self_check("07090402", "00020202"),
            firmware="unknown",
        ),
        _wave_client(
            "2920",
            CHAR_UUID_WAVEMINI_DATA,
            _WAVE_MINI_DATA,
            COMMAND_UUID_WAVE_MINI,
            command,
            firmware="unknown",
            silent_commands=silent,
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    first = await data.update_device(ble_device())
    second = await data.update_device(ble_device())

    expected = {AirthingsChip.BLE: "2.4.9", AirthingsChip.SUB: "2.2.2"}
    assert first.chip_versions == expected
    assert "battery" not in second.sensors
    assert second.chip_versions == expected


@pytest.mark.asyncio
async def test_self_check_clears_unset_sub_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a self-check without a SUB version clears the earlier one."""
    use_clients(
        monkeypatch,
        *(
            _wave_client(
                "2920",
                CHAR_UUID_WAVEMINI_DATA,
                _WAVE_MINI_DATA,
                COMMAND_UUID_WAVE_MINI,
                _wave_mini_self_check("07090402", sub_version),
            )
            for sub_version in ("00020202", "ffffffff")
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    first = await data.update_device(ble_device())
    second = await data.update_device(ble_device())

    assert first.chip_versions == {
        AirthingsChip.BLE: "1.5.3",
        AirthingsChip.SUB: "2.2.2",
    }
    assert second.chip_versions == {AirthingsChip.BLE: "1.5.3"}


def _wave_plus_self_check(msp_version: str) -> str:
    return f"6d00600c04000100{msp_version}11ff00000000c04c20001f3560007006B80B0900"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("msp_raw", "msp_versions"),
    [
        pytest.param("4085", {AirthingsChip.MSP: "2.5.1"}, id="new_version"),
        pytest.param("ffff", {}, id="not_reported"),
    ],
)
async def test_self_check_replaces_msp_version(
    monkeypatch: pytest.MonkeyPatch,
    msp_raw: str,
    msp_versions: dict[AirthingsChip, str],
) -> None:
    """Test a successful self-check replaces the earlier MSP version."""
    use_clients(
        monkeypatch,
        *(
            _wave_client(
                "2930",
                CHAR_UUID_WAVE_PLUS_DATA,
                _WAVE_PLUS_DATA,
                COMMAND_UUID_WAVE_PLUS,
                _wave_plus_self_check(msp),
            )
            for msp in ("0082", msp_raw)
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    first = await data.update_device(ble_device())
    second = await data.update_device(ble_device())

    assert first.chip_versions == _WAVE_PLUS_CHIP_VERSIONS
    assert second.chip_versions == {
        AirthingsChip.BLE: "1.5.3",
        AirthingsChip.SUB: "2.5.1",
        **msp_versions,
    }


@pytest.mark.asyncio
async def test_zero_firmware_revision_clears_ble_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a 0.0.0 firmware revision clears the BLE version of a Wave Plus."""
    use_clients(
        monkeypatch,
        *(
            _wave_client(
                "2930",
                CHAR_UUID_WAVE_PLUS_DATA,
                _WAVE_PLUS_DATA,
                COMMAND_UUID_WAVE_PLUS,
                _WAVE_PLUS_COMMAND,
                firmware=firmware,
            )
            for firmware in ("G-BLE-2.4.0", "G-BLE-0.0.0")
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    first = await data.update_device(ble_device())
    second = await data.update_device(ble_device())

    assert first.chip_versions == {
        AirthingsChip.BLE: "2.4.0",
        AirthingsChip.MSP: "2.2.0",
        AirthingsChip.SUB: "2.5.1",
    }
    assert second.chip_versions == {AirthingsChip.MSP: "2.2.0"}


@pytest.mark.asyncio
async def test_firmware_revision_ble_version_wins_every_sync(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test the firmware revision BLE version beats the self-check on every sync."""
    use_clients(
        monkeypatch,
        *(
            _wave_client(
                "2920",
                CHAR_UUID_WAVEMINI_DATA,
                _WAVE_MINI_DATA,
                COMMAND_UUID_WAVE_MINI,
                _wave_mini_self_check("07090402", "00020202"),
                firmware="M-BLE-2.4.0-master+0",
                failing=failing,
            )
            for failing in (set(), set(), {CHAR_UUID_FIRMWARE_REV}, set())
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    for _ in range(4):
        device = await data.update_device(ble_device())

        assert device.sw_version == "M-BLE-2.4.0-master+0"
        assert device.chip_versions == {
            AirthingsChip.BLE: "2.4.0",
            AirthingsChip.SUB: "2.2.2",
        }


@pytest.mark.asyncio
@pytest.mark.command_timeout
async def test_first_sync_without_revision_or_self_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test no chip versions are reported when nothing could be read."""
    monkeypatch.setattr("airthings_ble.parser.COMMAND_TIMEOUT", 0.01)
    use_clients(
        monkeypatch,
        _wave_client(
            "2920",
            CHAR_UUID_WAVEMINI_DATA,
            _WAVE_MINI_DATA,
            COMMAND_UUID_WAVE_MINI,
            _WAVE_MINI_COMMAND,
            failing={CHAR_UUID_FIRMWARE_REV},
            silent_commands=True,
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert device.sw_version == ""
    assert device.chip_versions == {}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("response", "message"),
    [
        (
            "6e00600c04000100008211ff00000000c04c20001f3560007006B80B0900",
            "Result for wrong command received, expected 6d got 6e",
        ),
        (
            "6d00600c04000100008211ff00000000c04c20001f3560007006B80B090000",
            "Wrong length data received (29) versus expected (28)",
        ),
    ],
)
async def test_rejected_wave_command_response_gives_no_battery(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    response: str,
    message: str,
) -> None:
    """Test a Wave command response that fails validation gives no battery."""
    use_clients(
        monkeypatch,
        _wave_client(
            "2930",
            CHAR_UUID_WAVE_PLUS_DATA,
            _WAVE_PLUS_DATA,
            COMMAND_UUID_WAVE_PLUS,
            response,
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert message in caplog.text
    assert "battery" not in device.sensors
    assert device.sensors["co2"] == 797.0
    assert device.chip_versions == {AirthingsChip.BLE: "1.5.3"}


@pytest.mark.asyncio
async def test_command_response_without_battery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a command response without a battery reading still sets chip versions."""
    monkeypatch.setitem(
        COMMAND_DECODERS, str(COMMAND_UUID_WAVE_PLUS), _NoBatteryCommandDecode()
    )
    use_clients(
        monkeypatch,
        _wave_client(
            "2930",
            CHAR_UUID_WAVE_PLUS_DATA,
            _WAVE_PLUS_DATA,
            COMMAND_UUID_WAVE_PLUS,
            _WAVE_PLUS_COMMAND,
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert "battery" not in device.sensors
    assert device.chip_versions == _WAVE_PLUS_CHIP_VERSIONS


class _NoBatteryCommandDecode(CommandDecode):
    format_type = "<L2BH2B9H"

    def decode_data(
        self, logger: logging.Logger, raw_data: bytearray | None
    ) -> dict[str, float | str | None] | None:
        return {AirthingsChip.MSP: "2.2.0"}


def _wave_plus_client(
    firmware: str = "G-BLE-1.5.3-master+0",
    command: str = _WAVE_PLUS_COMMAND,
    **kwargs: Any,
) -> FakeClient:
    return _wave_client(
        "2930",
        CHAR_UUID_WAVE_PLUS_DATA,
        _WAVE_PLUS_DATA,
        COMMAND_UUID_WAVE_PLUS,
        command,
        firmware=firmware,
        **kwargs,
    )


class _Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> _Clock:
    fake_clock = _Clock()
    monkeypatch.setattr("airthings_ble.parser._now", fake_clock)
    return fake_clock


_UPDATED_SUB_CHIP_VERSION = bytes.fromhex("720003000000")


@pytest.mark.asyncio
async def test_sub_chip_version_is_read_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test the SUB chip version is read on the first update and then cached."""
    first_client = _wave_plus_client()
    second_client = _wave_plus_client(
        sub_chip_version_response=bytes.fromhex("720003000000")
    )
    use_clients(monkeypatch, first_client, second_client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    first = await data.update_device(ble_device())
    second = await data.update_device(ble_device())

    assert first_client.writes == [_SELF_CHECK_REQUEST, SUB_CHIP_VERSION_REQUEST]
    assert second_client.writes == [_SELF_CHECK_REQUEST]
    assert first.chip_versions == _WAVE_PLUS_CHIP_VERSIONS
    assert second.chip_versions == _WAVE_PLUS_CHIP_VERSIONS
    assert not second_client.notifying


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("model", "data_uuid", "data", "command_uuid"),
    [
        pytest.param(
            "2930",
            CHAR_UUID_WAVE_PLUS_DATA,
            _WAVE_PLUS_DATA,
            COMMAND_UUID_WAVE_PLUS,
            id="wave_plus",
        ),
        pytest.param(
            "2950",
            CHAR_UUID_WAVE_2_DATA,
            _WAVE_RADON_DATA,
            COMMAND_UUID_WAVE_2,
            id="wave_radon",
        ),
    ],
)
@pytest.mark.parametrize(
    ("firmware", "sent"),
    [
        pytest.param("G-BLE-1.2.9-master+0", False, id="ble_1_2_9"),
        pytest.param("G-BLE-1.3.0-master+0", True, id="ble_1_3_0"),
        pytest.param("2.4.9", False, id="no_ble_version"),
    ],
)
async def test_sub_chip_version_needs_ble_1_3_0(
    monkeypatch: pytest.MonkeyPatch,
    model: str,
    data_uuid: UUID,
    data: str,
    command_uuid: UUID,
    firmware: str,
    sent: bool,
) -> None:
    """Test the SUB chip version is only requested from BLE firmware 1.3.0 on."""
    client = _wave_client(
        model, data_uuid, data, command_uuid, _WAVE_PLUS_COMMAND, firmware=firmware
    )
    use_clients(monkeypatch, client)
    parser = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await parser.update_device(ble_device())

    assert (SUB_CHIP_VERSION_REQUEST in client.writes) is sent
    assert (AirthingsChip.SUB in device.chip_versions) is sent


@pytest.mark.asyncio
async def test_wave_mini_does_not_request_sub_chip_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a Wave Mini gets its SUB chip version from the self-check only."""
    client = _wave_client(
        "2920",
        CHAR_UUID_WAVEMINI_DATA,
        _WAVE_MINI_DATA,
        COMMAND_UUID_WAVE_MINI,
        _WAVE_MINI_COMMAND,
    )
    use_clients(monkeypatch, client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    await data.update_device(ble_device())

    assert client.writes == [_SELF_CHECK_REQUEST]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "client_kwargs",
    [
        pytest.param({"sub_chip_version_response": None}, id="timeout"),
        pytest.param(
            {"sub_chip_version_error": BleakError("write failed")}, id="write_error"
        ),
        pytest.param({"sub_chip_version_error": TimeoutError()}, id="write_timeout"),
        pytest.param(
            {"sub_chip_version_response": bytes.fromhex("6d0002050100")},
            id="other_command_only",
        ),
        pytest.param(
            {"sub_chip_version_response": bytes.fromhex("720102050100")},
            id="error_status",
        ),
        pytest.param({"stall_sub_chip_version": True}, id="write_stall"),
        pytest.param({"start_notify_error": True}, id="start_notify_error"),
    ],
)
async def test_transient_sub_chip_version_failure_is_retried(
    monkeypatch: pytest.MonkeyPatch, client_kwargs: dict[str, Any]
) -> None:
    """Test a SUB chip version read that got no answer is retried on the next sync."""
    monkeypatch.setattr("airthings_ble.parser.CHIP_VERSION_TIMEOUT", 0.01)
    failing_client = _wave_plus_client(
        client_class=_SubChipVersionClient, **client_kwargs
    )
    retry_client = _wave_plus_client()
    use_clients(monkeypatch, failing_client, retry_client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER, max_attempts=1)

    failed = await data.update_device(ble_device())
    retried = await data.update_device(ble_device())

    assert failed.sensors[BATTERY] == 100
    assert failed.chip_versions == {
        AirthingsChip.BLE: "1.5.3",
        AirthingsChip.MSP: "2.2.0",
    }
    assert not failing_client.notifying
    assert retry_client.writes == [_SELF_CHECK_REQUEST, SUB_CHIP_VERSION_REQUEST]
    assert retried.chip_versions == _WAVE_PLUS_CHIP_VERSIONS


class _SubChipVersionClient(FakeClient):
    """Fails or stalls only the notification calls of the SUB chip version read."""

    def __init__(
        self,
        *args: Any,
        start_notify_error: bool = False,
        stop_notify_error_before: bool = False,
        stop_notify_error_after: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._sub_start_notify_error = start_notify_error
        self._sub_stop_notify_error_before = stop_notify_error_before
        self._sub_stop_notify_error_after = stop_notify_error_after
        self.start_notify_calls = 0

    async def start_notify(
        self, char_specifier: Any, callback: Callable[[Any, bytearray], None]
    ) -> None:
        self.start_notify_calls += 1
        if self._sub_start_notify_error and self.start_notify_calls == 2:
            raise BleakError("start failed")
        await super().start_notify(char_specifier, callback)

    async def stop_notify(self, char_specifier: Any) -> None:
        is_sub_session = self.writes[-1] == SUB_CHIP_VERSION_REQUEST
        if is_sub_session and self._sub_stop_notify_error_before:
            raise BleakError("stop failed")
        await super().stop_notify(char_specifier)
        if is_sub_session and self._sub_stop_notify_error_after:
            raise BleakError("stop failed")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "client_kwargs",
    [
        pytest.param({"stop_notify_error_before": True}, id="before_removal"),
        pytest.param({"stop_notify_error_after": True}, id="after_removal"),
    ],
)
async def test_failed_sub_chip_version_stop_notify_keeps_the_update(
    monkeypatch: pytest.MonkeyPatch, client_kwargs: dict[str, Any]
) -> None:
    """Test a failing stop_notify after the SUB chip version reply is not fatal."""
    client = _wave_plus_client(client_class=_SubChipVersionClient, **client_kwargs)
    use_clients(monkeypatch, client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER, max_attempts=1)

    device = await data.update_device(ble_device())

    assert device.sensors[BATTERY] == 100
    assert device.chip_versions == _WAVE_PLUS_CHIP_VERSIONS


@pytest.mark.asyncio
async def test_sub_chip_version_after_a_late_self_check_reply(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a late self-check notification does not hide the SUB chip version."""
    client = _wave_plus_client(
        sub_chip_version_response=[
            bytes.fromhex(_WAVE_PLUS_COMMAND),
            bytes.fromhex("720002050100"),
        ]
    )
    use_clients(monkeypatch, client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert device.chip_versions == _WAVE_PLUS_CHIP_VERSIONS
    assert device.sensors[BATTERY] == 100


@pytest.mark.asyncio
async def test_sub_chip_version_is_read_again_after_max_age(
    monkeypatch: pytest.MonkeyPatch, clock: _Clock
) -> None:
    """Test a SUB-only firmware update is picked up once the cache is too old."""
    clients = [
        _wave_plus_client(),
        _wave_plus_client(sub_chip_version_response=_UPDATED_SUB_CHIP_VERSION),
        _wave_plus_client(sub_chip_version_response=_UPDATED_SUB_CHIP_VERSION),
    ]
    use_clients(monkeypatch, *clients)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    first = await data.update_device(ble_device())
    clock.now += SUB_CHIP_VERSION_MAX_AGE - 1
    cached = await data.update_device(ble_device())
    clock.now += 1
    updated = await data.update_device(ble_device())

    assert [SUB_CHIP_VERSION_REQUEST in client.writes for client in clients] == [
        True,
        False,
        True,
    ]
    assert first.chip_versions == _WAVE_PLUS_CHIP_VERSIONS
    assert cached.chip_versions == _WAVE_PLUS_CHIP_VERSIONS
    assert updated.chip_versions == {
        **_WAVE_PLUS_CHIP_VERSIONS,
        AirthingsChip.SUB: "3.0.0",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("firmware", "command", "chip_versions"),
    [
        pytest.param(
            "G-BLE-1.6.0-master+0",
            _WAVE_PLUS_COMMAND,
            {AirthingsChip.BLE: "1.6.0", AirthingsChip.MSP: "2.2.0"},
            id="ble_change",
        ),
        pytest.param(
            "G-BLE-1.5.3-master+0",
            _wave_plus_self_check("4085"),
            {AirthingsChip.BLE: "1.5.3", AirthingsChip.MSP: "2.5.1"},
            id="msp_change",
        ),
    ],
)
@pytest.mark.parametrize(
    ("response", "sub_versions"),
    [
        pytest.param(
            _UPDATED_SUB_CHIP_VERSION, {AirthingsChip.SUB: "3.0.0"}, id="read"
        ),
        pytest.param(bytes.fromhex("720103000000"), {}, id="unsupported"),
    ],
)
async def test_sub_chip_version_is_read_again_after_chip_change(
    monkeypatch: pytest.MonkeyPatch,
    clock: _Clock,
    firmware: str,
    command: str,
    chip_versions: dict[AirthingsChip, str],
    response: bytes,
    sub_versions: dict[AirthingsChip, str],
) -> None:
    """Test a new BLE or MSP version triggers a new SUB chip version read."""
    updated_client = _wave_plus_client(
        firmware, command, sub_chip_version_response=response
    )
    use_clients(monkeypatch, _wave_plus_client(), updated_client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    await data.update_device(ble_device())
    device = await data.update_device(ble_device())

    assert updated_client.writes == [_SELF_CHECK_REQUEST, SUB_CHIP_VERSION_REQUEST]
    assert device.chip_versions == {**chip_versions, **sub_versions}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        pytest.param("7201", id="error_reply"),
        pytest.param("7200ff050100", id="version_not_set"),
        pytest.param("720000000000", id="all_zero"),
        pytest.param("720030303031", id="ascii_0001"),
    ],
)
async def test_unsupported_sub_chip_version_is_cached(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    clock: _Clock,
    response: str,
) -> None:
    """Test an unsupported SUB chip version is asked again only after the max age."""
    unsupported = bytes.fromhex(response)
    clients = [
        _wave_plus_client(sub_chip_version_response=unsupported),
        _wave_plus_client(sub_chip_version_response=unsupported),
        _wave_plus_client(),
    ]
    use_clients(monkeypatch, *clients)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    first = await data.update_device(ble_device())
    clock.now += SUB_CHIP_VERSION_MAX_AGE - 1
    second = await data.update_device(ble_device())
    clock.now += 1
    updated = await data.update_device(ble_device())

    assert [SUB_CHIP_VERSION_REQUEST in client.writes for client in clients] == [
        True,
        False,
        True,
    ]
    assert first.sensors[BATTERY] == 100
    assert first.chip_versions == {
        AirthingsChip.BLE: "1.5.3",
        AirthingsChip.MSP: "2.2.0",
    }
    assert second.chip_versions == first.chip_versions
    assert updated.chip_versions == _WAVE_PLUS_CHIP_VERSIONS
    unsupported_logs = [
        record
        for record in caplog.records
        if "SUB chip version not supported" in record.getMessage()
    ]
    assert [record.levelno for record in unsupported_logs] == [logging.DEBUG]


@pytest.mark.asyncio
async def test_stalled_sub_chip_version_write_is_bounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a stalled SUB chip version write gives up without a reconnect."""
    monkeypatch.setattr("airthings_ble.parser.CHIP_VERSION_TIMEOUT", 0.01)
    client = _wave_plus_client(stall_sub_chip_version=True)
    use_clients(monkeypatch, client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert device.sensors[BATTERY] == 100
    assert device.chip_versions == {
        AirthingsChip.BLE: "1.5.3",
        AirthingsChip.MSP: "2.2.0",
    }
    assert not client.notifying


@pytest.mark.asyncio
@pytest.mark.command_timeout
async def test_update_timeout_during_sub_chip_version_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test the update timeout during the SUB read stops notify after the self-check."""
    monkeypatch.setattr("airthings_ble.parser.UPDATE_TIMEOUT", 0.05)
    monkeypatch.setattr("airthings_ble.parser.CHIP_VERSION_TIMEOUT", 10)
    devices: list[AirthingsDevice] = []

    def recording_device() -> AirthingsDevice:
        devices.append(AirthingsDevice())
        return devices[-1]

    monkeypatch.setattr("airthings_ble.parser.AirthingsDevice", recording_device)
    stalled_client = _wave_plus_client(stall_sub_chip_version=True)
    silent_client = _wave_plus_client(silent_commands=True)
    use_clients(monkeypatch, stalled_client, silent_client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER, max_attempts=1)

    with pytest.raises(TimeoutError):
        await data.update_device(ble_device())

    assert devices[0].sensors[BATTERY] == 100
    assert not stalled_client.notifying
    assert stalled_client.disconnected

    monkeypatch.setattr("airthings_ble.parser.COMMAND_TIMEOUT", 0.01)
    monkeypatch.setattr("airthings_ble.parser.UPDATE_TIMEOUT", 1)
    device = await data.update_device(ble_device())

    assert device.chip_versions == {
        AirthingsChip.BLE: "1.5.3",
        AirthingsChip.MSP: "2.2.0",
    }


@pytest.mark.asyncio
async def test_unanswered_sub_chip_version_is_cached_after_three_attempts(
    monkeypatch: pytest.MonkeyPatch, clock: _Clock
) -> None:
    """Test a device that never answers is asked again only after the max age."""
    monkeypatch.setattr("airthings_ble.parser.CHIP_VERSION_TIMEOUT", 0.01)
    clients = [
        *(_wave_plus_client(sub_chip_version_response=None) for _ in range(3)),
        _wave_plus_client(),
        _wave_plus_client(),
    ]
    use_clients(monkeypatch, *clients)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    for _ in range(4):
        device = await data.update_device(ble_device())
        assert AirthingsChip.SUB not in device.chip_versions
    clock.now += SUB_CHIP_VERSION_MAX_AGE
    device = await data.update_device(ble_device())

    assert [SUB_CHIP_VERSION_REQUEST in client.writes for client in clients] == [
        True,
        True,
        True,
        False,
        True,
    ]
    assert device.chip_versions == _WAVE_PLUS_CHIP_VERSIONS


@pytest.mark.asyncio
async def test_unanswered_attempts_count_per_chip_versions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a BLE change restarts the count of unanswered SUB chip version reads."""
    monkeypatch.setattr("airthings_ble.parser.CHIP_VERSION_TIMEOUT", 0.01)
    clients = [
        *(_wave_plus_client(sub_chip_version_response=None) for _ in range(2)),
        *(
            _wave_plus_client("G-BLE-1.6.0-master+0", sub_chip_version_response=None)
            for _ in range(2)
        ),
        _wave_plus_client("G-BLE-1.6.0-master+0"),
    ]
    use_clients(monkeypatch, *clients)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    for _ in range(5):
        device = await data.update_device(ble_device())

    assert all(SUB_CHIP_VERSION_REQUEST in client.writes for client in clients)
    assert device.chip_versions[AirthingsChip.SUB] == "2.5.1"


@pytest.mark.asyncio
async def test_firmware_change_hides_the_old_sub_chip_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a failed read after a firmware change does not report the old SUB."""
    monkeypatch.setattr("airthings_ble.parser.CHIP_VERSION_TIMEOUT", 0.01)
    updated_client = _wave_plus_client(
        "G-BLE-1.6.0-master+0", sub_chip_version_response=None
    )
    retry_client = _wave_plus_client(
        "G-BLE-1.6.0-master+0", sub_chip_version_response=_UPDATED_SUB_CHIP_VERSION
    )
    use_clients(monkeypatch, _wave_plus_client(), updated_client, retry_client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    first = await data.update_device(ble_device())
    failed = await data.update_device(ble_device())
    retried = await data.update_device(ble_device())

    assert first.chip_versions == _WAVE_PLUS_CHIP_VERSIONS
    assert failed.chip_versions == {
        AirthingsChip.BLE: "1.6.0",
        AirthingsChip.MSP: "2.2.0",
    }
    assert retry_client.writes == [_SELF_CHECK_REQUEST, SUB_CHIP_VERSION_REQUEST]
    assert retried.chip_versions == {
        AirthingsChip.BLE: "1.6.0",
        AirthingsChip.MSP: "2.2.0",
        AirthingsChip.SUB: "3.0.0",
    }
