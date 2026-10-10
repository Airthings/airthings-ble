"""Passive parsing of Airthings BLE advertisements."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .const import AIRTHINGS_SHARED_SERVICE_UUID, AIRTHINGS_UNIQUE_SERVICE_UUID_TO_MODEL
from .device_type import AirthingsDeviceType

_SUPPORTED_SERIAL_PREFIXES: tuple[tuple[str, AirthingsDeviceType], ...] = (
    ("2900", AirthingsDeviceType.WAVE_GEN_1),
    ("2920", AirthingsDeviceType.WAVE_MINI),
    ("2930", AirthingsDeviceType.WAVE_PLUS),
    ("2950", AirthingsDeviceType.WAVE_RADON),
    ("3210", AirthingsDeviceType.WAVE_ENHANCE_EU),
    ("3220", AirthingsDeviceType.WAVE_ENHANCE_US),
    ("3250", AirthingsDeviceType.CORENTIUM_HOME_2),
)

_KNOWN_UNSUPPORTED_SERIAL_PREFIXES: tuple[tuple[str, str], ...] = (
    ("2960", "View Plus"),
    ("2980", "View Pollution"),
    ("2989", "View Radon"),
    ("281", "Hub"),
    ("282", "Hub"),
    ("410", "Renew"),
)


@dataclass(frozen=True, slots=True)
class AirthingsAdvertisementData:
    """Information available from an Airthings BLE advertisement."""

    model: AirthingsDeviceType | None = None
    serial_number: str | None = None
    model_code: str | None = None
    unsupported_name: str | None = None
    known_unsupported: bool = False

    @property
    def unknown(self) -> bool:
        """Return if the advertisement is Airthings, but not classified."""
        return self.model is None and not self.known_unsupported


def extract_serial_number_from_manufacturer_data(
    manufacturer_data: bytes | bytearray | None,
) -> str | None:
    """Extract the serial number from Airthings manufacturer data."""
    if manufacturer_data is None or len(manufacturer_data) < 4:
        return None
    return str(int.from_bytes(manufacturer_data[0:4], "little"))


def _serial_number(manufacturer_data: bytes | bytearray | None) -> str | None:
    serial_number = extract_serial_number_from_manufacturer_data(manufacturer_data)
    if serial_number is None or len(serial_number) != 10:
        return None
    if serial_number[0] not in {"2", "3", "4"}:
        return None
    return serial_number


def _model_from_service_uuids(
    service_uuids: Iterable[str] | None,
) -> AirthingsDeviceType | None:
    models = {
        AIRTHINGS_UNIQUE_SERVICE_UUID_TO_MODEL[uuid.lower()]
        for uuid in service_uuids or ()
        if uuid.lower() in AIRTHINGS_UNIQUE_SERVICE_UUID_TO_MODEL
    }
    return models.pop() if len(models) == 1 else None


def _has_shared_service_uuid(service_uuids: Iterable[str] | None) -> bool:
    return any(
        uuid.lower() == AIRTHINGS_SHARED_SERVICE_UUID for uuid in service_uuids or ()
    )


def _model_for_serial(serial_number: str) -> AirthingsDeviceType | None:
    for prefix, model in _SUPPORTED_SERIAL_PREFIXES:
        if serial_number.startswith(prefix):
            return model
    return None


def _unsupported_name_for_serial(serial_number: str) -> str | None:
    for prefix, name in _KNOWN_UNSUPPORTED_SERIAL_PREFIXES:
        if serial_number.startswith(prefix):
            return name
    return None


def _is_unsupported_local_name(local_name: str | None) -> bool:
    return local_name is not None and ("Renew" in local_name or "View" in local_name)


def parse_advertisement_data(
    local_name: str | None,
    manufacturer_data: bytes | bytearray | None,
    service_uuids: Iterable[str] | None = None,
) -> AirthingsAdvertisementData | None:
    """Classify an Airthings device from its advertisement, without connecting.

    `manufacturer_data` must be the payload for the Airthings company id (820).
    Returns None when nothing identifies the device as Airthings. Devices that
    are Airthings but not classified are reported as unknown, not unsupported,
    and still need an active read to be classified.
    """
    service_uuids = [uuid.lower() for uuid in service_uuids or ()]
    serial_number = _serial_number(manufacturer_data)
    model_code = serial_number[:4] if serial_number else None

    if serial_number is not None:
        if model := _model_for_serial(serial_number):
            return AirthingsAdvertisementData(
                model=model, serial_number=serial_number, model_code=model.value
            )
        if unsupported_name := _unsupported_name_for_serial(serial_number):
            return AirthingsAdvertisementData(
                serial_number=serial_number,
                model_code=model_code,
                unsupported_name=unsupported_name,
                known_unsupported=True,
            )

    if model := _model_from_service_uuids(service_uuids):
        return AirthingsAdvertisementData(
            model=model, serial_number=serial_number, model_code=model.value
        )

    has_shared_service_uuid = _has_shared_service_uuid(service_uuids)
    if has_shared_service_uuid and _is_unsupported_local_name(local_name):
        return AirthingsAdvertisementData(
            serial_number=serial_number,
            model_code=model_code,
            unsupported_name=local_name,
            known_unsupported=True,
        )

    if serial_number is None and not has_shared_service_uuid:
        return None

    return AirthingsAdvertisementData(
        serial_number=serial_number, model_code=model_code
    )
