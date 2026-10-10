"""Airthings firmware version handling."""

import re
from enum import Enum

_BLE_REVISION = re.compile(r"^[A-Z]-BLE-(\d+)\.(\d+)\.(\d+)(?:[-+]|$)")
_FIRST_BLE_VERSION_WITH_SUB_CHIP_VERSION = (1, 3, 0)


class AirthingsChip(str, Enum):
    """Chip in an Airthings device that runs its own firmware."""

    BLE = "BLE"
    MSP = "MSP"
    SUB = "SUB"


def _ble_version(revision: str) -> tuple[int, ...] | None:
    if not (match_obj := _BLE_REVISION.match(revision)):
        return None
    parts = tuple(int(part) for part in match_obj.groups())
    if any(part > 0xFF for part in parts) or not any(parts):
        return None
    return parts


def ble_version_from_revision(revision: str) -> str | None:
    """Extract the BLE chip version from a firmware revision string."""
    if (version := _ble_version(revision)) is None:
        return None
    return ".".join(str(part) for part in version)


def supports_sub_chip_version(revision: str) -> bool:
    """Check if the BLE firmware in the revision can report the SUB chip version."""
    version = _ble_version(revision)
    return version is not None and version >= _FIRST_BLE_VERSION_WITH_SUB_CHIP_VERSION


class AirthingsFirmwareVersion:
    """Firmware information for the Airthings device."""

    current_version: tuple[int, int, int] | None = None
    required_version: tuple[int, int, int] | None = None

    def __init__(
        self,
        current_version: str | None = None,
        required_version: str | None = None,
    ) -> None:
        self.current_version = self._version_as_tuple(current_version)
        self.required_version = self._version_as_tuple(required_version)

    def update_current_version(self, current_version: str | None) -> None:
        """Update the current version."""
        self.current_version = self._version_as_tuple(current_version)

    def update_required_version(self, required_version: str | None) -> None:
        """Update the required version."""
        self.required_version = self._version_as_tuple(required_version)

    def _version_as_tuple(self, version: str | None) -> tuple[int, int, int] | None:
        """Convert version string to tuple."""
        if not version:
            return None

        # Semantic version format: "X.Y.Z"
        if match_obj := re.match(r"^(\d+)\.(\d+)\.(\d+)$", version):
            major, minor, patch = match_obj.groups()
            return int(major), int(minor), int(patch)

        # Airthings version format:
        #  "T-SUB-2.6.0-master+0"
        #  "R-SUB-1.3.5-master+0"
        airthings_version = re.compile(r"^[A-Z]-SUB-(\d+)\.(\d+)\.(\d+)-.*")
        match_obj = airthings_version.match(version)
        if not match_obj:
            return None
        major, minor, patch = match_obj.groups()
        return int(major), int(minor), int(patch)

    @property
    def need_firmware_upgrade(self) -> bool:
        """Check if the device needs an update."""
        if not self.current_version or not self.required_version:
            return False

        return self.current_version < self.required_version
