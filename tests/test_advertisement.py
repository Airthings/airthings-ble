import pytest
from airthings_ble import (
    AirthingsConnectivityMode,
    AirthingsDeviceType,
    parse_advertisement_data,
)

_WAVE_GEN_1_UUID = "b42e1f6e-ade7-11e4-89d3-123b93f75cba"
_WAVE_PLUS_UUID = "b42e1c08-ade7-11e4-89d3-123b93f75cba"
_WAVE_MINI_UUID = "b42e3882-ade7-11e4-89d3-123b93f75cba"
_WAVE_RADON_UUID = "b42e4a8e-ade7-11e4-89d3-123b93f75cba"
_SHARED_UUID = "b42e90a2-ade7-11e4-89d3-123b93f75cba"
_EXACT_MODEL_CODES = {"2900", "2920", "2930", "2950"}
_RANGE_PREFIXES = {
    "321": AirthingsDeviceType.WAVE_ENHANCE_EU,
    "322": AirthingsDeviceType.WAVE_ENHANCE_US,
    "325": AirthingsDeviceType.CORENTIUM_HOME_2,
}


def _manufacturer_data(serial_number: int) -> bytes:
    """Build advertisement manufacturer data with an Airthings serial number."""
    return serial_number.to_bytes(4, "little") + b"\x00\x00"


@pytest.mark.parametrize(
    ("serial_number", "expected"),
    [
        (2900060343, AirthingsDeviceType.WAVE_GEN_1),
        (2920040229, AirthingsDeviceType.WAVE_MINI),
        (2930022176, AirthingsDeviceType.WAVE_PLUS),
        (2950020534, AirthingsDeviceType.WAVE_RADON),
        (3210000255, AirthingsDeviceType.WAVE_ENHANCE_EU),
        (3220000235, AirthingsDeviceType.WAVE_ENHANCE_US),
        (3250001289, AirthingsDeviceType.CORENTIUM_HOME_2),
    ],
)
def test_parse_advertisement_data_from_serial_number(
    serial_number: int, expected: AirthingsDeviceType
) -> None:
    """Test each supported model code in the serial number maps to its model."""
    result = parse_advertisement_data(
        manufacturer_data=_manufacturer_data(serial_number),
        service_uuids=[_SHARED_UUID],
    )

    assert result is not None
    assert result.model is expected
    assert result.serial_number == str(serial_number)


@pytest.mark.parametrize(
    ("service_uuid", "expected"),
    [
        (_WAVE_GEN_1_UUID, AirthingsDeviceType.WAVE_GEN_1),
        (_WAVE_PLUS_UUID, AirthingsDeviceType.WAVE_PLUS),
        (_WAVE_MINI_UUID, AirthingsDeviceType.WAVE_MINI),
        (_WAVE_RADON_UUID.upper(), AirthingsDeviceType.WAVE_RADON),
    ],
)
def test_parse_advertisement_data_from_unique_service_uuid(
    service_uuid: str, expected: AirthingsDeviceType
) -> None:
    """Test a service UUID unique to one model identifies it without a serial."""
    result = parse_advertisement_data(
        manufacturer_data=None, service_uuids=[service_uuid]
    )

    assert result is not None
    assert result.model is expected
    assert result.serial_number is None


def test_parse_advertisement_data_keeps_serial_with_unique_uuid() -> None:
    """Test the serial is kept when the model comes from a unique UUID."""
    result = parse_advertisement_data(
        manufacturer_data=_manufacturer_data(2910123456),
        service_uuids=iter([_WAVE_PLUS_UUID]),
    )

    assert result is not None
    assert result.model is AirthingsDeviceType.WAVE_PLUS
    assert result.serial_number == "2910123456"


def test_parse_advertisement_data_accepts_bytearray() -> None:
    """Test manufacturer data given as a bytearray is decoded like bytes."""
    result = parse_advertisement_data(
        manufacturer_data=bytearray(_manufacturer_data(3210123456)),
        service_uuids=None,
    )

    assert result is not None
    assert result.model is AirthingsDeviceType.WAVE_ENHANCE_EU
    assert result.serial_number == "3210123456"


@pytest.mark.parametrize(
    ("manufacturer_data", "service_uuids"),
    [
        (b"\x01\x02\x03", [_WAVE_MINI_UUID]),
        (b"\x01\x02\x03\x04", [_WAVE_MINI_UUID]),
        (None, [_WAVE_MINI_UUID, _WAVE_MINI_UUID]),
        (None, [_SHARED_UUID, _WAVE_MINI_UUID]),
        (None, ["0000180f-0000-1000-8000-00805f9b34fb", _WAVE_MINI_UUID]),
    ],
)
def test_parse_advertisement_data_unique_uuid_without_usable_serial(
    manufacturer_data: bytes | None, service_uuids: list[str]
) -> None:
    """Test a unique UUID identifies the model when the serial is unusable."""
    result = parse_advertisement_data(
        manufacturer_data=manufacturer_data, service_uuids=service_uuids
    )

    assert result is not None
    assert result.model is AirthingsDeviceType.WAVE_MINI
    assert result.serial_number is None


def test_parse_advertisement_data_serial_wins_over_unique_uuid() -> None:
    """Test the model code in the serial beats a unique UUID for another model."""
    result = parse_advertisement_data(
        manufacturer_data=_manufacturer_data(2920040229),
        service_uuids=[_WAVE_PLUS_UUID],
    )

    assert result is not None
    assert result.model is AirthingsDeviceType.WAVE_MINI


@pytest.mark.parametrize(
    ("manufacturer_data", "service_uuids"),
    [
        (None, None),
        (b"", [_SHARED_UUID]),
        (b"\x01\x02\x03", [_SHARED_UUID]),
        (b"\x01\x02\x03\x04\x00\x00", [_SHARED_UUID]),
        (bytearray(b"\x01\x02\x03\x04"), None),
        (_manufacturer_data(2960015842), [_SHARED_UUID]),
        (_manufacturer_data(2980002402), [_SHARED_UUID]),
        (_manufacturer_data(2810123456), ["b42e77de-ade7-11e4-89d3-123b93f75cba"]),
        (_manufacturer_data(4100000158), [_SHARED_UUID]),
        (_manufacturer_data(1102123456), None),
        (None, [_WAVE_PLUS_UUID, _WAVE_MINI_UUID]),
        (None, ["0000180f-0000-1000-8000-00805f9b34fb"]),
    ],
)
def test_parse_advertisement_data_ignores_everything_else(
    manufacturer_data: bytes | None, service_uuids: list[str] | None
) -> None:
    """Test anything not identified as a supported model returns None."""
    assert (
        parse_advertisement_data(
            manufacturer_data=manufacturer_data, service_uuids=service_uuids
        )
        is None
    )


@pytest.mark.parametrize(
    ("manufacturer_data", "expected"),
    [
        ("2097a4ae0b00", AirthingsDeviceType.WAVE_PLUS),
        ("9c7ca7ae0900", AirthingsDeviceType.WAVE_PLUS),
        ("7fb754bf0000", AirthingsDeviceType.WAVE_ENHANCE_EU),
        ("eb4dedbf0000", AirthingsDeviceType.WAVE_ENHANCE_US),
        ("394cedbf0000", AirthingsDeviceType.WAVE_ENHANCE_EU),
        ("e2416eb00000", None),
        ("969d6fb00000", None),
        ("623a9fb10000", None),
        ("9e0961f40000", None),
    ],
)
def test_parse_captured_advertisements(
    manufacturer_data: str, expected: AirthingsDeviceType | None
) -> None:
    """Test manufacturer data captured from real devices."""
    result = parse_advertisement_data(
        manufacturer_data=bytes.fromhex(manufacturer_data),
        service_uuids=[_SHARED_UUID],
    )

    assert (result.model if result else None) is expected


def test_parse_advertisement_data_only_classifies_supported_model_codes() -> None:
    """Test Wave needs its exact model code, Wave Enhance and Corentium Home 2 their range."""
    for model_code in map(str, range(1000, 4295)):
        result = parse_advertisement_data(
            manufacturer_data=_manufacturer_data(int(f"{model_code}000123")),
            service_uuids=[_SHARED_UUID],
        )

        if model_code in _EXACT_MODEL_CODES:
            assert result is not None, model_code
            assert result.model.value == model_code
        elif model_code[:3] in _RANGE_PREFIXES:
            assert result is not None, model_code
            assert result.model is _RANGE_PREFIXES[model_code[:3]]
        else:
            assert result is None, model_code


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


@pytest.mark.parametrize(
    ("serial_number", "flags", "expected"),
    [
        (2930022176, 0x000B, AirthingsConnectivityMode.BLE),
        (2930022176, 0x100B, AirthingsConnectivityMode.SMARTLINK),
        (2930022176, 0x5AA5, None),
        (2950020534, 0x0000, AirthingsConnectivityMode.BLE),
        (2950020534, 0x1000, AirthingsConnectivityMode.SMARTLINK),
        (2950020534, 0xF000, AirthingsConnectivityMode.SMARTLINK),
        (2950020534, 0x5AA5, None),
        (2920040229, 0x0000, AirthingsConnectivityMode.BLE),
        (2920040229, 0x1000, AirthingsConnectivityMode.SMARTLINK),
        (2920040229, 0x4000, None),
        (2920040229, 0x5000, None),
        (2920040229, 0x8000, None),
        (2920040229, 0x5AA5, None),
        (2900060343, 0x1000, None),
        (3210000255, 0x1000, None),
        (3220000235, 0x1000, None),
        (3250001289, 0x1000, None),
    ],
)
def test_parse_advertisement_data_connectivity_mode(
    serial_number: int, flags: int, expected: AirthingsConnectivityMode | None
) -> None:
    """Test the hub connected flag is decoded only where the model advertises it."""
    result = parse_advertisement_data(
        manufacturer_data=serial_number.to_bytes(4, "little")
        + flags.to_bytes(2, "little"),
        service_uuids=[_SHARED_UUID],
    )

    assert result is not None
    assert result.connectivity_mode is expected


@pytest.mark.parametrize(
    ("manufacturer_data", "expected"),
    [
        ("2097a4ae0b00", AirthingsConnectivityMode.BLE),
        ("9c7ca7ae0900", AirthingsConnectivityMode.BLE),
        ("7fb754bf0000", None),
        ("eb4dedbf0000", None),
    ],
)
def test_parse_captured_advertisements_connectivity_mode(
    manufacturer_data: str, expected: AirthingsConnectivityMode | None
) -> None:
    """Test the connectivity mode of manufacturer data captured from real devices."""
    result = parse_advertisement_data(
        manufacturer_data=bytes.fromhex(manufacturer_data),
        service_uuids=[_SHARED_UUID],
    )

    assert result is not None
    assert result.connectivity_mode is expected


@pytest.mark.parametrize(
    "manufacturer_data",
    [
        (2930022176).to_bytes(4, "little"),
        (2930022176).to_bytes(4, "little") + b"\x00",
        (2920040229).to_bytes(4, "little") + b"\x00",
    ],
)
def test_parse_advertisement_data_without_flags(manufacturer_data: bytes) -> None:
    """Test manufacturer data too short for the flags word has no connectivity mode."""
    result = parse_advertisement_data(
        manufacturer_data=manufacturer_data, service_uuids=[_SHARED_UUID]
    )

    assert result is not None
    assert result.connectivity_mode is None


@pytest.mark.parametrize(
    "manufacturer_data",
    [None, (2910123456).to_bytes(4, "little") + b"\x00\x10"],
)
def test_parse_advertisement_data_connectivity_mode_needs_serial_model(
    manufacturer_data: bytes | None,
) -> None:
    """Test a model identified only by service UUID has no connectivity mode."""
    result = parse_advertisement_data(
        manufacturer_data=manufacturer_data, service_uuids=[_WAVE_PLUS_UUID]
    )

    assert result is not None
    assert result.model is AirthingsDeviceType.WAVE_PLUS
    assert result.connectivity_mode is None
