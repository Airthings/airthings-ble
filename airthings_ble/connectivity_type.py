from enum import Enum


class AirthingsConnectivityMode(str, Enum):
    """Airthings connectivity modes."""

    UNKNOWN = "unknown"
    BLE = "Bluetooth"
    SMARTLINK = "Smartlink"

    @classmethod
    def from_atom_int(cls, value: int) -> "AirthingsConnectivityMode":
        """Get connectivity mode from integer value."""
        if value == 1:
            return cls.SMARTLINK
        if value == 4:
            return cls.BLE
        return cls.UNKNOWN

    @classmethod
    def from_wave_int(cls, value: int) -> "AirthingsConnectivityMode":
        """Get connectivity mode from Wave integer value."""
        if value == 0:
            return cls.BLE
        if value > 0:
            return cls.SMARTLINK
        return cls.UNKNOWN
