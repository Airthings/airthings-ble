"""Passive parsing of Airthings BLE advertisements."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .const import AIRTHINGS_UNIQUE_SERVICE_UUID_TO_MODEL
from .device_type import AirthingsDeviceType


@dataclass(frozen=True, slots=True)
class AirthingsAdvertisementData:
    """A supported Airthings device identified from its advertisement."""

    model: AirthingsDeviceType
    serial_number: str | None = None


def _serial_number(manufacturer_data: bytes | bytearray | None) -> str | None:
    if manufacturer_data is None or len(manufacturer_data) < 4:
        return None
    serial_number = str(int.from_bytes(manufacturer_data[0:4], "little"))
    if len(serial_number) != 10:
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


def parse_advertisement_data(
    manufacturer_data: bytes | bytearray | None,
    service_uuids: Iterable[str] | None = None,
) -> AirthingsAdvertisementData | None:
    """Identify a supported Airthings device from its advertisement, without connecting.

    `manufacturer_data` is the payload for the Airthings company id (820). The
    model comes from the model code in the serial number, or else from a service
    UUID unique to one model; `serial_number` is the advertised serial, if any.
    Returns None for everything else, including other Airthings products, so
    callers can skip the advertisement without connecting. None says nothing
    about later advertisements from the same address.
    """
    serial_number = _serial_number(manufacturer_data)
    if serial_number is not None and (
        model := AirthingsDeviceType.from_model_code(serial_number[:4])
    ):
        return AirthingsAdvertisementData(model=model, serial_number=serial_number)
    if model := _model_from_service_uuids(service_uuids):
        return AirthingsAdvertisementData(model=model, serial_number=serial_number)
    return None
