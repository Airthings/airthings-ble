"""Passive parsing helpers for Airthings BLE advertisements."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .const import (
    AIRTHINGS_SHARED_SERVICE_UUID,
    AIRTHINGS_UNIQUE_SERVICE_UUID_TO_MODEL,
)
from .device_type import AirthingsDeviceType

_KNOWN_UNSUPPORTED_MODEL_CODES: dict[str, str] = {
    "2810": "Hub",
    "2960": "View Plus",
    "2980": "View Pollution",
    "2989": "View Radon",
    "4100": "Renew",
}


@dataclass(frozen=True, slots=True)
class AirthingsAdvertisementData:
    """Parsed information available from an Airthings BLE advertisement."""

    model: AirthingsDeviceType | None = None
    serial_number: str | None = None
    model_code: str | None = None
    unsupported_name: str | None = None
    known_unsupported: bool = False

    @property
    def unknown(self) -> bool:
        """Return if the advertisement looks Airthings, but is not classified."""
        return self.model is None and not self.known_unsupported


def extract_serial_number_from_manufacturer_data(
    manufacturer_data: bytes | bytearray | None,
) -> str | None:
    """Extract the full serial number from manufacturer data when available."""
    if manufacturer_data is None or len(manufacturer_data) < 4:
        return None
    return str(int.from_bytes(manufacturer_data[0:4], "little"))


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


def _looks_like_airthings_serial_number(serial_number: str) -> bool:
    """Return if the parsed value looks like a real Airthings serial number."""
    return len(serial_number) == 10 and serial_number[0] in {"2", "3", "4"}


def _normalize_serial_number(
    manufacturer_data: bytes | bytearray | None,
) -> str | None:
    """Extract a plausible Airthings serial number from manufacturer data."""
    serial_number = extract_serial_number_from_manufacturer_data(manufacturer_data)
    if serial_number is None:
        return None
    if not _looks_like_airthings_serial_number(serial_number):
        return None
    return serial_number


def _model_code_from_serial_number(serial_number: str | None) -> str | None:
    """Extract a 4-digit Airthings model code from a normalized serial number."""
    if serial_number is None or len(serial_number) < 4:
        return None
    return serial_number[:4]


def _has_known_unsupported_name(local_name: str | None) -> bool:
    """Return if the local name identifies a known unsupported family."""
    return bool(local_name) and ("Renew" in local_name or "View" in local_name)


def _is_known_unsupported_serial_number(serial_number: str) -> bool:
    """Return if the serial number belongs to a known unsupported family."""
    model_code = _model_code_from_serial_number(serial_number)
    return model_code in _KNOWN_UNSUPPORTED_MODEL_CODES if model_code else False


def _unsupported_name_from_model_code(model_code: str | None) -> str | None:
    """Return the known unsupported family name for a model code."""
    if model_code is None:
        return None
    return _KNOWN_UNSUPPORTED_MODEL_CODES.get(model_code)


def parse_advertisement_data(
    local_name: str | None,
    manufacturer_data: bytes | bytearray | None,
    service_uuids: Iterable[str] | None = None,
) -> AirthingsAdvertisementData | None:
    """Parse advertisement data without connecting to the device."""
    serial_number = _normalize_serial_number(manufacturer_data)
    model_code = _model_code_from_serial_number(serial_number)
    if serial_number is not None:
        if model := AirthingsDeviceType.from_model_code(model_code or ""):
            return AirthingsAdvertisementData(
                model=model,
                serial_number=serial_number,
                model_code=model_code,
            )
        if _has_shared_service_uuid(service_uuids) and _is_known_unsupported_serial_number(
            serial_number
        ):
            return AirthingsAdvertisementData(
                serial_number=serial_number,
                model_code=model_code,
                unsupported_name=_unsupported_name_from_model_code(model_code),
                known_unsupported=True,
            )

    if _has_known_unsupported_name(local_name):
        return AirthingsAdvertisementData(
            serial_number=serial_number,
            model_code=model_code,
            unsupported_name=local_name,
            known_unsupported=True,
        )

    if model := _model_from_service_uuids(service_uuids):
        return AirthingsAdvertisementData(
            model=model,
            serial_number=serial_number,
            model_code=model_code,
        )

    if serial_number is None:
        return None

    return AirthingsAdvertisementData(
        serial_number=serial_number,
        model_code=model_code,
    )
