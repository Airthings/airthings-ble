from airthings_ble import (
    AIRTHINGS_SHARED_SERVICE_UUID,
    AirthingsDeviceType,
    extract_serial_number_from_manufacturer_data,
    parse_advertisement_data,
)


def _manufacturer_data(serial_number: int) -> bytes:
    """Build advertisement manufacturer data with an Airthings serial number."""
    return b"\xe4/" + serial_number.to_bytes(4, "little")


def test_extract_serial_number_from_manufacturer_data() -> None:
    """Test serial number extraction from manufacturer data."""
    assert (
        extract_serial_number_from_manufacturer_data(_manufacturer_data(2930123456))
        == "2930123456"
    )
    assert extract_serial_number_from_manufacturer_data(b"\xe4/") is None


def test_parse_supported_advertisement_data_from_serial_number() -> None:
    """Test passive parsing of a supported advertisement."""
    result = parse_advertisement_data(
        local_name="Generic Airthings",
        manufacturer_data=_manufacturer_data(3210123456),
        service_uuids=[AIRTHINGS_SHARED_SERVICE_UUID],
    )

    assert result is not None
    assert result.model is AirthingsDeviceType.WAVE_ENHANCE_EU
    assert result.serial_number == "3210123456"
    assert result.known_unsupported is False


def test_parse_known_unsupported_advertisement_data_from_serial_number() -> None:
    """Test passive parsing rejects unsupported devices from serial range."""
    result = parse_advertisement_data(
        local_name="Generic Airthings",
        manufacturer_data=_manufacturer_data(2960123456),
        service_uuids=[AIRTHINGS_SHARED_SERVICE_UUID],
    )

    assert result is not None
    assert result.model is None
    assert result.serial_number == "2960123456"
    assert result.known_unsupported is True


def test_parse_known_unsupported_advertisement_data_from_name() -> None:
    """Test passive parsing rejects unsupported devices from the local name."""
    result = parse_advertisement_data(
        local_name="Airthings View Plus",
        manufacturer_data=None,
        service_uuids=[AIRTHINGS_SHARED_SERVICE_UUID],
    )

    assert result is not None
    assert result.model is None
    assert result.serial_number is None
    assert result.known_unsupported is True
