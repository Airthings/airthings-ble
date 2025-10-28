from enum import Enum


class AirthingsConnectivityType(Enum):
    """Airthings connectivity types."""

    UNKNOWN = "unknown"
    BLE = "ble"
    SMARTLINK = "smartlink"

    def __new__(cls, value: str) -> "AirthingsConnectivityType":
        """Create new connectivity type."""
        obj = object.__new__(cls)
        obj.raw_value = value
        return obj

    @classmethod
    def from_int(cls, value: int) -> "AirthingsConnectivityType":
        """Get connectivity type from integer value."""
        if value == 1:
            return AirthingsConnectivityType.SMARTLINK
        if value == 4:
            return AirthingsConnectivityType.BLE
        return AirthingsConnectivityType.UNKNOWN
