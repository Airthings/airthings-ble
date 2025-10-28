"""Airthings connectivity types."""

from enum import Enum


class AirthingsConnectivityMode(str, Enum):
    """Airthings connectivity modes."""

    BLE = "Bluetooth"
    SMARTLINK = "Smartlink"
    UNKNOWN = "unknown"

    @classmethod
    def from_int(cls, value: int) -> "AirthingsConnectivityMode":
        """Get connectivity mode from integer value."""
        if value == 1:
            return cls.SMARTLINK
        if value == 4:
            return cls.BLE
        return cls.UNKNOWN
