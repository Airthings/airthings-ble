"""Parser for Airthings BLE advertisements."""

from __future__ import annotations

from .airthings_firmware import AirthingsChipVersions
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
    "AirthingsBluetoothDeviceData",
    "AirthingsChipVersions",
    "AirthingsConnectivityMode",
    "AirthingsDevice",
    "AirthingsDeviceType",
    "DisconnectedError",
    "UnsupportedDeviceError",
]
