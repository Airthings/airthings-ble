"""Passive parsing of Airthings BLE advertisements."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .connectivity_mode import AirthingsConnectivityMode
from .const import (
    ADVERTISEMENT_FLAG_SMARTLINK,
    ADVERTISEMENT_FLAGS_NO_HUB_SUPPORT,
    ADVERTISEMENT_FLAGS_UNPOPULATED,
    AIRTHINGS_UNIQUE_SERVICE_UUID_TO_MODEL,
    WAVE_MINI_MODELS,
    WAVE_PLUS_AND_RADON_MODELS,
)
from .device_type import AirthingsDeviceType

_RANGE_PREFIXES: tuple[tuple[str, AirthingsDeviceType], ...] = (
    ("321", AirthingsDeviceType.WAVE_ENHANCE_EU),
    ("322", AirthingsDeviceType.WAVE_ENHANCE_US),
    ("325", AirthingsDeviceType.CORENTIUM_HOME_2),
)


@dataclass(frozen=True, slots=True)
class AirthingsAdvertisementData:
    """A supported Airthings device identified from its advertisement."""

    model: AirthingsDeviceType
    serial_number: str | None = None
    connectivity_mode: AirthingsConnectivityMode | None = None


def _serial_number(manufacturer_data: bytes | bytearray | None) -> str | None:
    if manufacturer_data is None or len(manufacturer_data) < 4:
        return None
    serial_number = str(int.from_bytes(manufacturer_data[0:4], "little"))
    if len(serial_number) != 10:
        return None
    return serial_number


def _flags(manufacturer_data: bytes | bytearray | None) -> int | None:
    if manufacturer_data is None or len(manufacturer_data) < 6:
        return None
    return int.from_bytes(manufacturer_data[4:6], "little")


def _connectivity_mode(
    model: AirthingsDeviceType, flags: int | None
) -> AirthingsConnectivityMode | None:
    if flags is None:
        return None
    if model in WAVE_PLUS_AND_RADON_MODELS:
        if flags == ADVERTISEMENT_FLAGS_UNPOPULATED:
            return None
    elif model in WAVE_MINI_MODELS:
        if flags & ADVERTISEMENT_FLAGS_NO_HUB_SUPPORT:
            return None
    else:
        return None
    if flags & ADVERTISEMENT_FLAG_SMARTLINK:
        return AirthingsConnectivityMode.SMARTLINK
    return AirthingsConnectivityMode.BLE


def _model_from_serial_number(serial_number: str) -> AirthingsDeviceType | None:
    if model := AirthingsDeviceType.from_model_code(serial_number[:4]):
        return model
    for prefix, model in _RANGE_PREFIXES:
        if serial_number.startswith(prefix):
            return model
    return None


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
    model comes from the serial number (the exact model code, or the whole
    serial range for Wave Enhance and Corentium Home 2), or else from a service
    UUID unique to one model; `serial_number` is the advertised serial, if any.
    Returns None for everything else, including other Airthings products, so
    callers can skip the advertisement without connecting. None says nothing
    about later advertisements from the same address.

    `connectivity_mode` is SMARTLINK when a Wave Plus, Wave Radon or Wave Mini
    advertises that it is connected to an Airthings hub, BLE when it advertises
    that it is not, and None when the advertisement does not say: other models,
    a model identified only by service UUID, a Wave Mini firmware without hub
    support, flags the device has not filled in yet, or data too short to carry
    them. None means unknown, not BLE. Do not poll a SmartLink device over BLE:
    Airthings' own app only connects to one for pairing and settings.
    """
    serial_number = _serial_number(manufacturer_data)
    if serial_number is not None and (
        model := _model_from_serial_number(serial_number)
    ):
        return AirthingsAdvertisementData(
            model=model,
            serial_number=serial_number,
            connectivity_mode=_connectivity_mode(model, _flags(manufacturer_data)),
        )
    if model := _model_from_service_uuids(service_uuids):
        return AirthingsAdvertisementData(model=model, serial_number=serial_number)
    return None
