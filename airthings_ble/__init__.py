"""Parser for Airthings BLE advertisements."""

from __future__ import annotations

from .device_type import AirthingsDeviceType
from .parser import AirthingsBluetoothDeviceData, AirthingsDevice

__version__ = "0.9.1"

__all__ = ["AirthingsBluetoothDeviceData", "AirthingsDevice", "AirthingsDeviceType"]
