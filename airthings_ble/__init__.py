"""Parser for Airthings BLE advertisements."""

from __future__ import annotations

from .parser import AirthingsBluetoothDeviceData, AirthingsDevice
from .device_type import AirthingsDeviceType

__version__ = "0.7.0"

__all__ = ["AirthingsBluetoothDeviceData", "AirthingsDevice", "AirthingsDeviceType"]
