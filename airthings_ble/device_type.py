"""Airthings device types."""

from enum import Enum

from airthings_ble.airthings_firmware import AirthingsFirmwareVersion


class AirthingsDeviceType(Enum):
    """Airthings device types."""

    UNKNOWN = "0"
    WAVE_GEN_1 = "2900"
    WAVE_MINI = "2920"
    WAVE_PLUS = "2930"
    WAVE_RADON = "2950"
    WAVE_ENHANCE_EU = "3210"
    WAVE_ENHANCE_US = "3220"
    CORENTIUM_HOME_2 = "3250"

    raw_value: str  # pylint: disable=invalid-name

    def __new__(cls, value: str) -> "AirthingsDeviceType":
        """Create new device type."""
        obj = object.__new__(cls)
        obj.raw_value = value
        return obj

    @classmethod
    def atom_devices(cls) -> list["AirthingsDeviceType"]:
        """Get list of Airthings Atom devices."""
        return [
            AirthingsDeviceType.WAVE_ENHANCE_EU,
            AirthingsDeviceType.WAVE_ENHANCE_US,
            AirthingsDeviceType.CORENTIUM_HOME_2,
        ]

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
    # pylint: disable=too-many-return-statements
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
        if self in (
            AirthingsDeviceType.WAVE_ENHANCE_EU,
            AirthingsDeviceType.WAVE_ENHANCE_US,
        ):
            return "Wave Enhance"
        if self == AirthingsDeviceType.CORENTIUM_HOME_2:
            return "Corentium Home 2"
        return "Unknown"

    def battery_percentage(self, voltage: float) -> int:
        """Calculate battery percentage based on voltage."""
        if self == AirthingsDeviceType.WAVE_MINI:
            return round(self._three_batteries(voltage))
        return round(self._two_batteries(voltage))

    # pylint: disable=too-many-return-statements
    def _two_batteries(self, voltage: float) -> float:
        if voltage >= 3.00:
            return 100
        if 2.80 <= voltage < 3.00:
            return self._interpolate(
                voltage=voltage, voltage_range=(2.80, 3.00), percentage_range=(81, 100)
            )
        if 2.60 <= voltage < 2.80:
            return self._interpolate(
                voltage=voltage, voltage_range=(2.60, 2.80), percentage_range=(53, 81)
            )
        if 2.50 <= voltage < 2.60:
            return self._interpolate(
                voltage=voltage, voltage_range=(2.50, 2.60), percentage_range=(28, 53)
            )
        if 2.20 <= voltage < 2.50:
            return self._interpolate(
                voltage=voltage, voltage_range=(2.20, 2.50), percentage_range=(5, 28)
            )
        if 2.10 <= voltage < 2.20:
            return self._interpolate(
                voltage=voltage, voltage_range=(2.10, 2.20), percentage_range=(0, 5)
            )
        return 0

    # pylint: disable=too-many-return-statements
    def _three_batteries(self, voltage: float) -> float:
        if voltage >= 4.50:
            return 100
        if 4.20 <= voltage < 4.50:
            return self._interpolate(
                voltage=voltage, voltage_range=(4.20, 4.50), percentage_range=(85, 100)
            )
        if 3.90 <= voltage < 4.20:
            return self._interpolate(
                voltage=voltage, voltage_range=(3.90, 4.20), percentage_range=(62, 85)
            )
        if 3.75 <= voltage < 3.90:
            return self._interpolate(
                voltage=voltage, voltage_range=(3.75, 3.90), percentage_range=(42, 62)
            )
        if 3.30 <= voltage < 3.75:
            return self._interpolate(
                voltage=voltage, voltage_range=(3.30, 3.75), percentage_range=(23, 42)
            )
        if 2.40 <= voltage < 3.30:
            return self._interpolate(
                voltage=voltage, voltage_range=(2.40, 3.30), percentage_range=(0, 23)
            )
        return 0

    def _interpolate(
        self,
        voltage: float,
        voltage_range: tuple[float, float],
        percentage_range: tuple[int, int],
    ) -> float:
        return (voltage - voltage_range[0]) / (voltage_range[1] - voltage_range[0]) * (
            percentage_range[1] - percentage_range[0]
        ) + percentage_range[0]

    def need_firmware_upgrade(self, current_version: str) -> "AirthingsFirmwareVersion":
        """Check if the device needs an update."""
        version = AirthingsFirmwareVersion(current_version=current_version)

        if self in (
            AirthingsDeviceType.WAVE_ENHANCE_EU,
            AirthingsDeviceType.WAVE_ENHANCE_US,
        ):
            version.update_required_version("T-SUB-2.6.1-master+0")
            return version

        if self == AirthingsDeviceType.CORENTIUM_HOME_2:
            version.update_required_version("R-SUB-1.3.4-master+0")

        return version
