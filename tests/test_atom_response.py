import logging

import pytest
from airthings_ble.atom.request_path import AtomRequestPath
from airthings_ble.atom.response import AtomResponse

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def test_atom_response_wave_enhance_latest_values() -> None:
    """Test the Wave Enhance request."""
    random_bytes = bytes.fromhex("A1B2")

    response = AtomResponse(
        logger=_LOGGER,
        response=bytes.fromhex(
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


def test_atom_response_corentium_home_2_latest_values() -> None:
    """Test the Wave Enhance request."""
    random_bytes = bytes.fromhex("CCA4")

    response = AtomResponse(
        logger=_LOGGER,
        response=bytes.fromhex(
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


def test_atom_response_corentium_home_2_connectivity_mode() -> None:
    """Test the Wave Enhance request."""
    random_bytes = bytes.fromhex("5F93")

    response = AtomResponse(
        logger=_LOGGER,
        response=bytes.fromhex("10010003455F9381A2006A31372F302F33313130300204"),
        random_bytes=random_bytes,
        path=AtomRequestPath.CONNECTIVITY_MODE,
    )

    data = response.parse()
    assert data is not None

    assert data == {"connectivity_mode": "ble"}


def test_empty_response() -> None:
    """Test the Wave Enhance request."""
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
    ],
)
def test_invalid_responses(response: bytes, exception: str) -> None:
    """Test the Wave Enhance request."""
    random_bytes = bytes.fromhex("1234")

    atom_response = AtomResponse(
        logger=_LOGGER,
        response=response,
        random_bytes=random_bytes,
        path=AtomRequestPath.LATEST_VALUES,
    )
    try:
        atom_response.parse()
    except ValueError as exc:
        assert str(exc) == exception
