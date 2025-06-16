"""Airthings firmware version handling."""

import re


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
        if re.match(r"^\d+\.\d+\.\d+$", version):
            semantic_version = re.compile(r"(\d+)\.(\d+)\.(\d+)")
            match_obj = semantic_version.match(version)
            if not match_obj:
                return None
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
