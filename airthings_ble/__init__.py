"""Parser for Airthings BLE advertisements."""

from __future__ import annotations

from .connectivity_mode import AirthingsConnectivityMode
from .device_type import AirthingsDeviceType
from .parser import (
    AirthingsBluetoothDeviceData,
    AirthingsDevice,
    UnsupportedDeviceError,
)

__version__ = "1.1.1"

__all__ = [
    "AirthingsBluetoothDeviceData",
    "AirthingsConnectivityMode",
    "AirthingsDevice",
    "AirthingsDeviceType",
    "UnsupportedDeviceError",
]
