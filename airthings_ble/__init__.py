"""Parser for Airthings BLE advertisements."""

from __future__ import annotations

from .advertisement import (
    AirthingsAdvertisementData,
    extract_serial_number_from_manufacturer_data,
    parse_advertisement_data,
)
from .connectivity_mode import AirthingsConnectivityMode
from .const import AIRTHINGS_SERVICE_UUIDS, AIRTHINGS_SHARED_SERVICE_UUID
from .device_type import AirthingsDeviceType
from .parser import (
    AirthingsBluetoothDeviceData,
    AirthingsDevice,
    DisconnectedError,
    UnsupportedDeviceError,
)

__version__ = "1.2.0"

__all__ = [
    "AIRTHINGS_SERVICE_UUIDS",
    "AIRTHINGS_SHARED_SERVICE_UUID",
    "AirthingsAdvertisementData",
    "AirthingsBluetoothDeviceData",
    "AirthingsConnectivityMode",
    "AirthingsDevice",
    "AirthingsDeviceType",
    "DisconnectedError",
    "UnsupportedDeviceError",
    "extract_serial_number_from_manufacturer_data",
    "parse_advertisement_data",
]
