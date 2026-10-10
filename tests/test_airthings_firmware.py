from airthings_ble.airthings_firmware import (
    AirthingsFirmwareVersion,
    ble_version_from_revision,
)
from pytest import mark


def test_airthings_firmware_need_upgrade() -> None:
    fw = AirthingsFirmwareVersion(
        current_version="T-SUB-2.6.0-master+0",
        required_version="T-SUB-2.6.1-master+0",
    )
    assert fw.need_firmware_upgrade is True


def test_airthings_firmware_need_upgrade_semantic() -> None:
    fw = AirthingsFirmwareVersion(
        current_version="1.3.4",
        required_version="1.3.5",
    )
    assert fw.need_firmware_upgrade is True
    assert fw.current_version == (1, 3, 4)
    assert fw.required_version == (1, 3, 5)


def test_airthings_firmware_no_upgrade() -> None:
    fw = AirthingsFirmwareVersion(
        current_version="R-SUB-1.3.5-master+0",
        required_version="R-SUB-1.3.5-master+0",
    )
    assert fw.need_firmware_upgrade is False
    assert fw.current_version == (1, 3, 5)
    assert fw.required_version == (1, 3, 5)


def test_airthings_firmware_no_required_firmware() -> None:
    fw = AirthingsFirmwareVersion(
        current_version="T-SUB-1.0.1-master+0",
        required_version=None,
    )
    assert fw.need_firmware_upgrade is False
    assert fw.current_version == (1, 0, 1)
    assert fw.required_version is None


@mark.parametrize(
    "invalid_version",
    [
        "a.b.c",
        "1.2",
        "1.a.3",
        "invalid",
        None,
    ],
)
def test_airthings_firmware_invalid_current_version(invalid_version: str) -> None:
    fw = AirthingsFirmwareVersion(
        current_version=invalid_version,
        required_version="T-SUB-1.0.1-master+0",
    )
    assert fw.current_version is None
    assert fw.required_version == (1, 0, 1)
    assert fw.need_firmware_upgrade is False


def test_airthings_firmware_invalid_required_version() -> None:
    fw = AirthingsFirmwareVersion(
        current_version="G-SUB-1.0.1-master+0",
        required_version="invalid",
    )
    assert fw.need_firmware_upgrade is False
    assert fw.current_version == (1, 0, 1)
    assert fw.required_version is None


@mark.parametrize(
    ("revision", "version"),
    [
        ("G-BLE-2.4.0-master+0", "2.4.0"),
        ("G-BLE-1.0.0", "1.0.0"),
        ("G-BLE-1.10.12-beta+001", "1.10.12"),
        ("G-BLE-1.0.0+5", "1.0.0"),
        ("G-BLE-255.255.255", "255.255.255"),
        ("M-BLE-999.2.3", None),
        ("M-BLE-1.256.3-master+0", None),
        ("T-SUB-2.6.0-master+0", None),
        ("G-MSP-1.0.0", None),
        ("G-BLE-1.0.0.1", None),
        ("1.0.0", None),
        ("", None),
    ],
)
def test_ble_version_from_revision(revision: str, version: str | None) -> None:
    assert ble_version_from_revision(revision) == version
