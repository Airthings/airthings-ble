"""Airthings device types."""
from enum import Enum


class AirthingsDeviceType(Enum):
    """Airthings device types."""

    UNKNOWN = 0
    WAVE_GEN_1 = "2900"
    WAVE_MINI = "2920"
    WAVE_PLUS = "2930"
    WAVE_RADON = "2950"

    raw_value: str  # pylint: disable=invalid-name

    def __new__(cls, value: str) -> "AirthingsDeviceType":
        """Create new device type."""
        obj = object.__new__(cls)
        obj.raw_value = value
        return obj

    @classmethod
    def from_raw_value(cls, value: str) -> "AirthingsDeviceType":
        """Get device type from raw value."""
        for device_type in cls:
            if device_type.value == value:
                device_type.raw_value = value
                return device_type
        unknown_device = AirthingsDeviceType.UNKNOWN
        unknown_device.raw_value = value
        return unknown_device

    @property
    def product_name(self) -> str:
        """Get product name."""
        if self == AirthingsDeviceType.WAVE_GEN_1:
            return "Wave Gen 1"
        if self == AirthingsDeviceType.WAVE_MINI:
            return "Wave Mini"
        if self == AirthingsDeviceType.WAVE_PLUS:
            return "Wave Plus"
        if self == AirthingsDeviceType.WAVE_RADON:
            return "Wave Radon"
        return "Unknown"

    def battery_percentage(self, vin: float) -> int:
        """Calculate battery percentage based on voltage."""
        if self == AirthingsDeviceType.WAVE_MINI:
            return self._battery_percentage_wave_mini(vin)
        return self._battery_percentage_wave_radon_and_plus(vin)

    # pylint: disable=too-many-return-statements
    def _battery_percentage_wave_radon_and_plus(self, vin: float) -> int:
        if vin >= 3.00:
            return 100
        if 2.80 <= vin < 3.00:
            return int((vin - 2.80) / (3.00 - 2.80) * (100 - 81) + 81)
        if 2.60 <= vin < 2.80:
            return int((vin - 2.60) / (2.80 - 2.60) * (81 - 53) + 53)
        if 2.50 <= vin < 2.60:
            return int((vin - 2.50) / (2.60 - 2.50) * (53 - 28) + 28)
        if 2.20 <= vin < 2.50:
            return int((vin - 2.20) / (2.50 - 2.20) * (28 - 5) + 5)
        if 2.10 <= vin < 2.20:
            return int((vin - 2.10) / (2.20 - 2.10) * (5 - 0) + 0)
        return 0

    # pylint: disable=too-many-return-statements
    def _battery_percentage_wave_mini(self, vin: float) -> int:
        if vin >= 4.50:
            return 100
        if 4.20 <= vin < 4.50:
            return int((vin - 4.20) / (4.50 - 4.20) * (100 - 85) + 85)
        if 3.90 <= vin < 4.20:
            return int((vin - 3.90) / (4.20 - 3.90) * (85 - 62) + 62)
        if 3.75 <= vin < 3.90:
            return int((vin - 3.75) / (3.90 - 3.75) * (62 - 42) + 42)
        if 3.30 <= vin < 3.75:
            return int((vin - 3.30) / (3.75 - 3.30) * (42 - 23) + 23)
        if 2.40 <= vin < 3.30:
            return int((vin - 2.40) / (3.30 - 2.40) * (23 - 0) + 0)
        return 0
