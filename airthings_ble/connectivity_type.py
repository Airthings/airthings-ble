from enum import Enum


class AirthingsConnectivityType(str, Enum):
    """Airthings connectivity types."""

    UNKNOWN = "unknown"
    BLE = "ble"
    SMARTLINK = "smartlink"

    @classmethod
    def from_int(cls, value: int) -> "AirthingsConnectivityType":
        """Get connectivity type from integer value."""
        if value == 1:
            return cls.SMARTLINK
        if value == 4:
            return cls.BLE
        return cls.UNKNOWN
