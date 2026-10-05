import logging

import pytest
from airthings_ble.atom.request_path import AtomRequestPath
from airthings_ble.atom.response import AtomResponse
from airthings_ble.command_decode import AtomCommandDecode
from airthings_ble.connectivity_mode import AirthingsConnectivityMode

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@pytest.mark.parametrize("buffer_type", [bytes, bytearray])
def test_atom_response_wave_enhance_latest_values(
    buffer_type: type[bytes | bytearray],
) -> None:
    """Test Wave Enhance latest values."""
    random_bytes = bytes.fromhex("A1B2")

    response = AtomResponse(
        logger=_LOGGER,
        response=buffer_type.fromhex(
            "1001000345a1b281a2006d32393939392f302f333130313202583ea9634e4f49"
            + "182763544d501972f06348554d190d2f63434f321902dc63564f43190115634c5"
            + "55801635052531a005f364663424154190b346354494d1876"
        ),
        random_bytes=random_bytes,
        path=AtomRequestPath.LATEST_VALUES,
    )

    sensor_data = response.parse()
    assert sensor_data is not None

    assert sensor_data["TMP"] == 29424
    assert sensor_data["HUM"] == 3375
    assert sensor_data["CO2"] == 732
    assert sensor_data["VOC"] == 277
    assert sensor_data["LUX"] == 1
    assert sensor_data["PRS"] == 6239814
    assert sensor_data["BAT"] == 2868
    assert sensor_data["TIM"] == 118
    assert sensor_data["NOI"] == 39


@pytest.mark.parametrize("buffer_type", [bytes, bytearray])
def test_atom_response_corentium_home_2_latest_values(
    buffer_type: type[bytes | bytearray],
) -> None:
    """Test Corentium Home 2 latest values."""
    random_bytes = bytes.fromhex("CCA4")

    response = AtomResponse(
        logger=_LOGGER,
        response=buffer_type.fromhex(
            "1001000345CCA481A2006D32393939392F302F3331303132025831A863523234"
            + "0363523744076352333007635231591263544D501973D76348554D190D8C63424"
            + "154190B816354494D19061D"
        ),
        random_bytes=random_bytes,
        path=AtomRequestPath.LATEST_VALUES,
    )

    sensor_data = response.parse()
    assert sensor_data is not None

    assert sensor_data["TMP"] == 29655
    assert sensor_data["HUM"] == 3468
    assert sensor_data["BAT"] == 2945
    assert sensor_data["TIM"] == 1565
    assert sensor_data["R24"] == 3
    assert sensor_data["R7D"] == 7
    assert sensor_data["R30"] == 7
    assert sensor_data["R1Y"] == 18


@pytest.mark.parametrize("buffer_type", [bytes, bytearray])
def test_atom_response_corentium_home_2_connectivity_mode(
    buffer_type: type[bytes | bytearray],
) -> None:
    """Test Corentium Home 2 connectivity mode response."""
    random_bytes = bytes.fromhex("5F93")

    response = AtomResponse(
        logger=_LOGGER,
        response=buffer_type.fromhex("10010003455F9381A2006A31372F302F33313130300204"),
        random_bytes=random_bytes,
        path=AtomRequestPath.CONNECTIVITY_MODE,
    )

    data = response.parse()
    assert data is not None

    assert data == {"connectivity_mode": "Bluetooth"}


def test_empty_response() -> None:
    """Test empty atom request."""
    random_bytes = bytes.fromhex("1234")

    with pytest.raises(ValueError):
        AtomResponse(
            logger=_LOGGER,
            response=None,
            random_bytes=random_bytes,
            path=AtomRequestPath.LATEST_VALUES,
        )


@pytest.mark.parametrize(
    "response,exception",
    [
        (
            bytes.fromhex("00000003455F9381A2006A31372F302F33313130300204"),
            "Invalid response header",
        ),
        (
            bytes.fromhex("10010003455F9381A2006A31372F302F33313130300204"),
            "Invalid response checksum",
        ),
        (
            bytes.fromhex("1001000345123482A2006A31372F302F33313130300204"),
            "Invalid response type",
        ),
        (
            bytes.fromhex("100100034512348181006A31372F302F33313130300204"),
            "Invalid response array length",
        ),
        (
            bytes.fromhex("10010003451234"),
            "Response too short",
        ),
        (
            bytes.fromhex("1001000345123481"),
            "Response too short",
        ),
        (
            bytes.fromhex("1001000345123481A2006A31372F302F333131"),
            "Invalid CBOR data",
        ),
        (
            bytes.fromhex("1001000345123481A2006D32393939392F302F33313031320241A1"),
            "Invalid CBOR data",
        ),
        (
            bytes.fromhex("1001000345123481A2006A31372F302F33313130300204"),
            "Response path does not match request path",
        ),
        (
            bytes.fromhex("1001000345123481A20161780204"),
            "Response path missing",
        ),
        (
            bytes.fromhex("1001000345123481A2006D32393939392F302F33313031320104"),
            "Response data missing",
        ),
        (
            bytes.fromhex("1001000345123481A2006D32393939392F302F33313031320204"),
            "Invalid response data type",
        ),
        (
            bytes.fromhex("1001000345123481A2006D32393939392F302F333130313202428102"),
            "Invalid response data type",
        ),
    ],
)
def test_invalid_responses(response: bytes, exception: str) -> None:
    """Test invalid atom response."""
    random_bytes = bytes.fromhex("1234")

    atom_response = AtomResponse(
        logger=_LOGGER,
        response=response,
        random_bytes=random_bytes,
        path=AtomRequestPath.LATEST_VALUES,
    )
    with pytest.raises(ValueError, match=f"^{exception}$"):
        atom_response.parse()


def test_atom_response_connectivity_mode_not_configured() -> None:
    """Test connectivity mode 0 is reported as not configured."""
    response = AtomResponse(
        logger=_LOGGER,
        response=bytes.fromhex("10010003455F9381A2006A31372F302F33313130300200"),
        random_bytes=bytes.fromhex("5F93"),
        path=AtomRequestPath.CONNECTIVITY_MODE,
    )

    assert response.parse() == {
        "connectivity_mode": AirthingsConnectivityMode.NOT_CONFIGURED.value
    }


@pytest.mark.parametrize("payload", [b"", b"\x81"])
def test_atom_command_decode_short_response(payload: bytes) -> None:
    """Test a truncated Atom response decodes to None instead of raising."""
    decoder = AtomCommandDecode(url=AtomRequestPath.LATEST_VALUES)
    raw_data = bytearray.fromhex("1001000345") + decoder.request.random_bytes + payload

    assert decoder.decode_data(logger=_LOGGER, raw_data=raw_data) is None


def test_atom_response_latest_values_as_map() -> None:
    """Test latest values sent as a CBOR map rather than wrapped bytes."""
    response = AtomResponse(
        logger=_LOGGER,
        response=bytes.fromhex(
            "1001000345123481A2006D32393939392F302F333130313202A163544D501972F0"
        ),
        random_bytes=bytes.fromhex("1234"),
        path=AtomRequestPath.LATEST_VALUES,
    )

    assert response.parse() == {"TMP": 29424}


def test_atom_response_connectivity_mode_not_an_integer() -> None:
    """Test a connectivity mode that is not an integer is rejected."""
    response = AtomResponse(
        logger=_LOGGER,
        response=bytes.fromhex("10010003455F9381A2006A31372F302F333131303002617A"),
        random_bytes=bytes.fromhex("5F93"),
        path=AtomRequestPath.CONNECTIVITY_MODE,
    )

    with pytest.raises(ValueError, match="^Invalid response data type$"):
        response.parse()
