"""Parser for Airthings BLE advertisements."""

from __future__ import annotations

from .advertisement import (
    AirthingsAdvertisementData,
    parse_advertisement_data,
)
from .battery_status import AirthingsBatteryStatus
from .connectivity_mode import AirthingsConnectivityMode
from .device_type import AirthingsDeviceType
from .parser import (
    AirthingsBluetoothDeviceData,
    AirthingsDevice,
    DisconnectedError,
    UnsupportedDeviceError,
)

__version__ = "1.3.0rc1"

__all__ = [
    "AirthingsAdvertisementData",
    "AirthingsBatteryStatus",
    "AirthingsBluetoothDeviceData",
    "AirthingsConnectivityMode",
    "AirthingsDevice",
    "AirthingsDeviceType",
    "DisconnectedError",
    "UnsupportedDeviceError",
    "parse_advertisement_data",
]
