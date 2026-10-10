import pytest
from airthings_ble import (
    AIRTHINGS_SHARED_SERVICE_UUID,
    AirthingsDeviceType,
    extract_serial_number_from_manufacturer_data,
    parse_advertisement_data,
)


def _manufacturer_data(serial_number: int) -> bytes:
    """Build advertisement manufacturer data with an Airthings serial number."""
    return serial_number.to_bytes(4, "little") + b"\x00\x00"


def test_extract_serial_number_from_manufacturer_data() -> None:
    """Test serial number extraction from manufacturer data."""
    assert (
        extract_serial_number_from_manufacturer_data(_manufacturer_data(2930123456))
        == "2930123456"
    )
    assert extract_serial_number_from_manufacturer_data(b"\xe4/\x00") is None
    assert (
        extract_serial_number_from_manufacturer_data(
            bytearray(_manufacturer_data(3210123456))
        )
        == "3210123456"
    )


def test_parse_advertisement_data_ignores_invalid_serial_shape() -> None:
    """Test payloads that decode but do not look like Airthings serials are ignored."""
    result = parse_advertisement_data(
        local_name=None,
        manufacturer_data=b"\x01\x02\x03\x04\x00\x00",
        service_uuids=None,
    )

    assert result is None


@pytest.mark.parametrize("manufacturer_data", [None, b"", b"\x01", b"\x01\x02\x03\x04"])
def test_parse_advertisement_data_shared_uuid_without_serial_is_unknown(
    manufacturer_data: bytes | None,
) -> None:
    """Test the shared service UUID alone marks an unclassified Airthings device."""
    result = parse_advertisement_data(
        local_name=None,
        manufacturer_data=manufacturer_data,
        service_uuids=[AIRTHINGS_SHARED_SERVICE_UUID],
    )

    assert result is not None
    assert result.serial_number is None
    assert result.unknown is True


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
    assert result.model_code == "2960"
    assert result.unsupported_name == "View Plus"
    assert result.known_unsupported is True
    assert result.unknown is False


def test_parse_known_unsupported_hub_advertisement_data_from_serial_number() -> None:
    """Test passive parsing rejects hub devices from serial range."""
    result = parse_advertisement_data(
        local_name="Generic Airthings",
        manufacturer_data=_manufacturer_data(2810123456),
        service_uuids=[AIRTHINGS_SHARED_SERVICE_UUID],
    )

    assert result is not None
    assert result.model is None
    assert result.serial_number == "2810123456"
    assert result.model_code == "2810"
    assert result.unsupported_name == "Hub"
    assert result.known_unsupported is True
    assert result.unknown is False


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
    assert result.model_code is None
    assert result.unsupported_name == "Airthings View Plus"
    assert result.known_unsupported is True
    assert result.unknown is False


def test_parse_known_unsupported_advertisement_data_from_name_with_bad_serial() -> None:
    """Test unsupported-name fallback keeps no model code for invalid serials."""
    result = parse_advertisement_data(
        local_name="Renew AP-1",
        manufacturer_data=b"\x01\x02\x03\x04\x00\x00",
        service_uuids=[AIRTHINGS_SHARED_SERVICE_UUID],
    )

    assert result is not None
    assert result.model is None
    assert result.serial_number is None
    assert result.model_code is None
    assert result.unsupported_name == "Renew AP-1"
    assert result.known_unsupported is True
    assert result.unknown is False


def test_parse_advertisement_data_ignores_non_serial_manufacturer_payload() -> None:
    """Test shared UUID devices are not rejected on non-serial payloads."""
    result = parse_advertisement_data(
        local_name="Corentium Home 2",
        manufacturer_data=bytes.fromhex("c6 15 b7 c1 00 00"),
        service_uuids=[AIRTHINGS_SHARED_SERVICE_UUID],
    )

    assert result is not None
    assert result.model is AirthingsDeviceType.CORENTIUM_HOME_2
    assert result.serial_number == "3250001350"
    assert result.model_code == "3250"
    assert result.unsupported_name is None
    assert result.known_unsupported is False
    assert result.unknown is False


def test_parse_advertisement_data_identifies_tern_from_serial_number() -> None:
    """Test shared UUID devices use the serial prefix instead of the local name."""
    result = parse_advertisement_data(
        local_name="Airthings Tern CO2",
        manufacturer_data=bytes.fromhex("e0 cb 54 bf 00 00"),
        service_uuids=[AIRTHINGS_SHARED_SERVICE_UUID],
    )

    assert result is not None
    assert result.model is AirthingsDeviceType.WAVE_ENHANCE_EU
    assert result.serial_number == "3210005472"
    assert result.model_code == "3210"
    assert result.unsupported_name is None
    assert result.known_unsupported is False
    assert result.unknown is False


def test_parse_advertisement_data_keeps_unlisted_ranges_unknown() -> None:
    """Test a serial range that is not listed stays unknown, not unsupported."""
    result = parse_advertisement_data(
        local_name="Airthings Tern CO2",
        manufacturer_data=_manufacturer_data(3300002645),
        service_uuids=[AIRTHINGS_SHARED_SERVICE_UUID],
    )

    assert result is not None
    assert result.model is None
    assert result.serial_number == "3300002645"
    assert result.model_code == "3300"
    assert result.unsupported_name is None
    assert result.known_unsupported is False
    assert result.unknown is True


def test_parse_advertisement_data_keeps_other_wave_plus_ranges_unknown() -> None:
    """Test a serial outside the exact supported model codes is not rejected."""
    result = parse_advertisement_data(
        local_name="Airthings Wave+",
        manufacturer_data=_manufacturer_data(2910123456),
        service_uuids=None,
    )

    assert result is not None
    assert result.model is None
    assert result.known_unsupported is False
    assert result.unknown is True


def test_parse_supported_advertisement_data_from_unique_service_uuid() -> None:
    """Test passive parsing can classify older devices from a unique UUID."""
    result = parse_advertisement_data(
        local_name=None,
        manufacturer_data=None,
        service_uuids=["b42e1c08-ade7-11e4-89d3-123b93f75cba"],
    )

    assert result is not None
    assert result.model is AirthingsDeviceType.WAVE_PLUS
    assert result.serial_number is None
    assert result.model_code == "2930"
    assert result.unsupported_name is None
    assert result.known_unsupported is False
    assert result.unknown is False


def test_parse_advertisement_data_returns_serial_only_for_unknown_serial() -> None:
    """Test passive parsing keeps the serial when the type is still unknown."""
    result = parse_advertisement_data(
        local_name=None,
        manufacturer_data=_manufacturer_data(3990123456),
        service_uuids=None,
    )

    assert result is not None
    assert result.model is None
    assert result.serial_number == "3990123456"
    assert result.model_code == "3990"
    assert result.unsupported_name is None
    assert result.known_unsupported is False
    assert result.unknown is True


def test_parse_advertisement_data_unique_uuid_wins_for_unknown_serial() -> None:
    """Test a unique legacy UUID still identifies the device model."""
    result = parse_advertisement_data(
        local_name=None,
        manufacturer_data=_manufacturer_data(3990123456),
        service_uuids=["b42e3882-ade7-11e4-89d3-123b93f75cba"],
    )

    assert result is not None
    assert result.model is AirthingsDeviceType.WAVE_MINI
    assert result.serial_number == "3990123456"
    assert result.model_code == "2920"
    assert result.unsupported_name is None
    assert result.known_unsupported is False
    assert result.unknown is False


def test_parse_advertisement_data_returns_none_for_ambiguous_service_uuids() -> None:
    """Test passive parsing does not guess when multiple unique UUIDs conflict."""
    result = parse_advertisement_data(
        local_name=None,
        manufacturer_data=None,
        service_uuids=[
            "b42e1c08-ade7-11e4-89d3-123b93f75cba",
            "b42e3882-ade7-11e4-89d3-123b93f75cba",
        ],
    )

    assert result is None


def test_parse_advertisement_data_returns_none_without_identifiers() -> None:
    """Test passive parsing returns None when the advertisement has no signals."""
    result = parse_advertisement_data(
        local_name=None,
        manufacturer_data=None,
        service_uuids=None,
    )

    assert result is None


_WAVE_PLUS_UUID = "b42e1c08-ade7-11e4-89d3-123b93f75cba"


@pytest.mark.parametrize(
    ("local_name", "manufacturer_data", "service_uuid", "expected"),
    [
        ("Airthings Wave+", "2097a4ae0b00", _WAVE_PLUS_UUID, ("2930022176", "2930")),
        ("Airthings Wave+", "9c7ca7ae0900", _WAVE_PLUS_UUID, ("2930211996", "2930")),
        ("Airthings View Plus", "e2416eb00000", None, ("2960015842", "View Plus")),
        ("Airthings View Plus", "969d6fb00000", None, ("2960104854", "View Plus")),
        (
            "Airthings View Pollu",
            "623a9fb10000",
            None,
            ("2980002402", "View Pollution"),
        ),
        ("Airthings Tern CO2", "7fb754bf0000", None, ("3210000255", "3210")),
        ("Airthings Tern CO2", "eb4dedbf0000", None, ("3220000235", "3220")),
        ("Airthings Tern CO2", "394cedbf0000", None, ("3219999801", None)),
        ("Renew AP-1", "9e0961f40000", None, ("4100000158", "Renew")),
    ],
)
def test_parse_captured_advertisements(
    local_name: str,
    manufacturer_data: str,
    service_uuid: str | None,
    expected: tuple[str, str | None],
) -> None:
    """Test advertisements captured from real devices."""
    serial_number, classification = expected
    result = parse_advertisement_data(
        local_name=local_name,
        manufacturer_data=bytes.fromhex(manufacturer_data),
        service_uuids=[service_uuid or AIRTHINGS_SHARED_SERVICE_UUID],
    )

    assert result is not None
    assert result.serial_number == serial_number
    if classification is None:
        assert result.unknown is True
    elif classification.isdigit():
        assert result.model is AirthingsDeviceType(classification)
    else:
        assert result.known_unsupported is True
        assert result.unsupported_name == classification


@pytest.mark.parametrize(
    ("model_code", "expected"),
    [
        ("2930", AirthingsDeviceType.WAVE_PLUS),
        ("3250", AirthingsDeviceType.CORENTIUM_HOME_2),
        ("0", None),
        ("3219", None),
        ("", None),
    ],
)
def test_from_model_code(model_code: str, expected: AirthingsDeviceType | None) -> None:
    """Test model code lookup never returns UNKNOWN."""
    assert AirthingsDeviceType.from_model_code(model_code) is expected


def test_parse_advertisement_data_ignores_serials_outside_ble_ranges() -> None:
    """Test a ten digit serial outside the BLE product ranges is ignored."""
    result = parse_advertisement_data(
        local_name=None,
        manufacturer_data=_manufacturer_data(1102123456),
        service_uuids=None,
    )

    assert result is None


def test_parse_advertisement_data_accepts_service_uuid_iterator() -> None:
    """Test service UUIDs given as a one-shot iterator are all considered."""
    result = parse_advertisement_data(
        local_name=None,
        manufacturer_data=_manufacturer_data(2910123456),
        service_uuids=iter(["b42e1c08-ade7-11e4-89d3-123b93f75cba"]),
    )

    assert result is not None
    assert result.model is AirthingsDeviceType.WAVE_PLUS


def test_parse_advertisement_data_ignores_other_brands_named_view() -> None:
    """Test a non-Airthings device named like an unsupported model is ignored."""
    result = parse_advertisement_data(
        local_name="Living Room View TV",
        manufacturer_data=None,
        service_uuids=["0000180f-0000-1000-8000-00805f9b34fb"],
    )

    assert result is None


_SUPPORTED_PREFIXES = ("2900", "2920", "2930", "2950", "3210", "3220", "3250")
_UNSUPPORTED_PREFIXES = ("2960", "2980", "2989", "281", "282", "410")


def test_parse_advertisement_data_never_classifies_other_serial_ranges() -> None:
    """Test every other serial range is unknown, never a model or unsupported."""
    for model_code in map(str, range(2000, 4295)):
        if model_code.startswith(_SUPPORTED_PREFIXES + _UNSUPPORTED_PREFIXES):
            continue
        result = parse_advertisement_data(
            local_name="Airthings device",
            manufacturer_data=_manufacturer_data(int(f"{model_code}000123")),
            service_uuids=[AIRTHINGS_SHARED_SERVICE_UUID],
        )

        assert result is not None, model_code
        assert result.model is None, model_code
        assert result.known_unsupported is False, model_code
        assert result.unknown is True, model_code


@pytest.mark.parametrize(
    ("serial_number", "expected"),
    [
        (2900060343, AirthingsDeviceType.WAVE_GEN_1),
        (2920040229, AirthingsDeviceType.WAVE_MINI),
        (2950020534, AirthingsDeviceType.WAVE_RADON),
        (3210000255, AirthingsDeviceType.WAVE_ENHANCE_EU),
        (3220000235, AirthingsDeviceType.WAVE_ENHANCE_US),
        (3250001289, AirthingsDeviceType.CORENTIUM_HOME_2),
    ],
)
def test_parse_advertisement_data_maps_model_codes(
    serial_number: int, expected: AirthingsDeviceType
) -> None:
    """Test each supported model code maps to its model and model code."""
    result = parse_advertisement_data(
        local_name=None,
        manufacturer_data=_manufacturer_data(serial_number),
        service_uuids=None,
    )

    assert result is not None
    assert result.model is expected
    assert result.model_code == expected.value


@pytest.mark.parametrize(
    ("serial_number", "service_uuids", "expected"),
    [
        (2810123456, ["b42e77de-ade7-11e4-89d3-123b93f75cba"], "Hub"),
        (2820123456, None, "Hub"),
        (2960123456, None, "View Plus"),
        (2980123456, None, "View Pollution"),
        (2989123456, None, "View Radon"),
        (4100123456, None, "Renew"),
    ],
)
def test_parse_advertisement_data_unsupported_serial_without_shared_uuid(
    serial_number: int, service_uuids: list[str] | None, expected: str
) -> None:
    """Test an unsupported serial range is recognised whatever UUIDs are advertised."""
    result = parse_advertisement_data(
        local_name=None,
        manufacturer_data=_manufacturer_data(serial_number),
        service_uuids=service_uuids,
    )

    assert result is not None
    assert result.known_unsupported is True
    assert result.unsupported_name == expected


def test_parse_advertisement_data_unique_uuid_wins_over_unsupported_name() -> None:
    """Test a supported model's unique UUID beats a name that looks unsupported."""
    result = parse_advertisement_data(
        local_name="View from the kitchen",
        manufacturer_data=b"",
        service_uuids=[_WAVE_PLUS_UUID, AIRTHINGS_SHARED_SERVICE_UUID],
    )

    assert result is not None
    assert result.model is AirthingsDeviceType.WAVE_PLUS
    assert result.known_unsupported is False


def test_parse_advertisement_data_name_needs_shared_uuid() -> None:
    """Test the unsupported-name fallback is not applied without the shared UUID."""
    result = parse_advertisement_data(
        local_name="Airthings View Plus",
        manufacturer_data=b"\x01\x02",
        service_uuids=None,
    )

    assert result is None


@pytest.mark.parametrize("serial_number", [2988123456, 2931123456, 2961123456])
def test_parse_advertisement_data_other_four_digit_codes_are_unknown(
    serial_number: int,
) -> None:
    """Test Wave and View serials outside their exact model codes stay unknown."""
    result = parse_advertisement_data(
        local_name=None,
        manufacturer_data=_manufacturer_data(serial_number),
        service_uuids=[AIRTHINGS_SHARED_SERVICE_UUID],
    )

    assert result is not None
    assert result.unknown is True
