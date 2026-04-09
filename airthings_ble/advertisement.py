"""Passive parsing helpers for Airthings BLE advertisements."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .const import (
    AIRTHINGS_SHARED_SERVICE_UUID,
    AIRTHINGS_UNIQUE_SERVICE_UUID_TO_MODEL,
)
from .device_type import AirthingsDeviceType

_SUPPORTED_SERIAL_PREFIX_TO_MODEL: dict[str, AirthingsDeviceType] = {
    AirthingsDeviceType.WAVE_GEN_1.value: AirthingsDeviceType.WAVE_GEN_1,
    AirthingsDeviceType.WAVE_MINI.value: AirthingsDeviceType.WAVE_MINI,
    AirthingsDeviceType.WAVE_PLUS.value: AirthingsDeviceType.WAVE_PLUS,
    AirthingsDeviceType.WAVE_RADON.value: AirthingsDeviceType.WAVE_RADON,
    AirthingsDeviceType.WAVE_ENHANCE_EU.value: AirthingsDeviceType.WAVE_ENHANCE_EU,
    AirthingsDeviceType.WAVE_ENHANCE_US.value: AirthingsDeviceType.WAVE_ENHANCE_US,
    AirthingsDeviceType.CORENTIUM_HOME_2.value: AirthingsDeviceType.CORENTIUM_HOME_2,
}


@dataclass(frozen=True, slots=True)
class AirthingsAdvertisementData:
    """Parsed information available from an Airthings BLE advertisement."""

    model: AirthingsDeviceType | None = None
    serial_number: str | None = None
    known_unsupported: bool = False


def extract_serial_number_from_manufacturer_data(
    manufacturer_data: bytes | bytearray | None,
) -> str | None:
    """Extract the full serial number from manufacturer data when available."""
    if manufacturer_data is None or len(manufacturer_data) < 6:
        return None
    return str(int.from_bytes(manufacturer_data[2:6], "little"))


def _model_from_service_uuids(
    service_uuids: Iterable[str] | None,
) -> AirthingsDeviceType | None:
    """Resolve models that can be identified from unique service UUIDs."""
    if service_uuids is None:
        return None

    resolved_models = {
        AIRTHINGS_UNIQUE_SERVICE_UUID_TO_MODEL[service_uuid.lower()]
        for service_uuid in service_uuids
        if service_uuid.lower() in AIRTHINGS_UNIQUE_SERVICE_UUID_TO_MODEL
    }
    if len(resolved_models) != 1:
        return None
    return resolved_models.pop()


def _has_shared_service_uuid(service_uuids: Iterable[str] | None) -> bool:
    """Return if the advertisement uses the shared newer Airthings UUID."""
    if service_uuids is None:
        return False
    return any(
        service_uuid.lower() == AIRTHINGS_SHARED_SERVICE_UUID
        for service_uuid in service_uuids
    )


def parse_advertisement_data(
    local_name: str | None,
    manufacturer_data: bytes | bytearray | None,
    service_uuids: Iterable[str] | None = None,
) -> AirthingsAdvertisementData | None:
    """Parse advertisement data without connecting to the device."""
    serial_number = extract_serial_number_from_manufacturer_data(manufacturer_data)
    if serial_number is not None:
        serial_prefix = serial_number[:4]
        if serial_prefix in _SUPPORTED_SERIAL_PREFIX_TO_MODEL:
            return AirthingsAdvertisementData(
                model=_SUPPORTED_SERIAL_PREFIX_TO_MODEL[serial_prefix],
                serial_number=serial_number,
            )
        if _has_shared_service_uuid(service_uuids):
            return AirthingsAdvertisementData(
                serial_number=serial_number,
                known_unsupported=True,
            )

    if local_name and ("Renew" in local_name or "View" in local_name):
        return AirthingsAdvertisementData(
            serial_number=serial_number,
            known_unsupported=True,
        )

    if model := _model_from_service_uuids(service_uuids):
        return AirthingsAdvertisementData(model=model, serial_number=serial_number)

    if serial_number is None:
        return None

    return AirthingsAdvertisementData(serial_number=serial_number)
