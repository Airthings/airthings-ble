"""Airthings connectivity types."""

from enum import Enum


class AirthingsConnectivityMode(str, Enum):
    """Airthings connectivity modes."""

    NOT_CONFIGURED = "Not configured"
    BLE = "Bluetooth"
    SMARTLINK = "SmartLink"
    UNKNOWN = "unknown"

    @classmethod
    def from_atom_int(cls, value: int) -> "AirthingsConnectivityMode":
        """Get connectivity mode from integer value."""
        if value == 0:
            return cls.NOT_CONFIGURED
        if value == 1:
            return cls.SMARTLINK
        if value == 4:
            return cls.BLE
        return cls.UNKNOWN
