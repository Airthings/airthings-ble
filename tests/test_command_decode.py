import logging

import pytest
from airthings_ble.atom.request_path import AtomRequestPath
from airthings_ble.command_decode import (
    AtomCommandDecode,
    CommandDecode,
    WaveMiniCommandDecode,
    WaveRadonAndPlusCommandDecode,
)
from airthings_ble.const import BATTERY, BLE_VERSION, MSP_VERSION, SUB_VERSION

_LOGGER = logging.getLogger(__name__)

_WAVE_PLUS = "6d00600c04000100008211ff00000000c04c20001f3560007006B80B0900"
_WAVE_MINI = "6d0064000000c800000001020304f4015802bc02000020038403b80b4c04b0040000"


@pytest.mark.parametrize(
    ("decoder", "response"),
    [
        (WaveRadonAndPlusCommandDecode(), _WAVE_PLUS),
        (WaveMiniCommandDecode(), _WAVE_MINI),
    ],
)
@pytest.mark.parametrize(
    ("mangle", "message"),
    [
        (lambda data: None, "No data received"),
        (lambda data: b"\x6e" + data[1:], "expected 6d got 6e"),
        (lambda data: data[:-1], "Wrong length data received"),
        (lambda data: data + b"\x00", "Wrong length data received"),
    ],
)
def test_rejected_wave_command_response(
    caplog: pytest.LogCaptureFixture,
    decoder: CommandDecode,
    response: str,
    mangle,
    message: str,
) -> None:
    """Test a Wave command response that fails validation decodes to None."""
    caplog.set_level(logging.DEBUG)
    raw_data = mangle(bytearray.fromhex(response))

    assert decoder.decode_data(logger=_LOGGER, raw_data=raw_data) is None
    assert message in caplog.text


def test_base_command_decoder_returns_no_values() -> None:
    """Test the base command decoder reports no values."""
    assert CommandDecode().decode_data(_LOGGER, bytearray(b"\x6d")) == {}


def _wave_plus_response(device_type: str, msp_version: str) -> bytearray:
    return bytearray.fromhex(
        f"6d00600c0400{device_type}00{msp_version}11ff00000000c04c20001f3560007006b80b0900"
    )


@pytest.mark.parametrize(
    ("device_type", "raw_version", "version"),
    [
        pytest.param("02", "4085", "2.5.1", id="wave_plus"),
        pytest.param("01", "0082", "2.2.0", id="wave_radon"),
        pytest.param("02", "3f7f", "1.63.0", id="build_bits_ignored"),
        pytest.param("02", "c804", "2018-12-04", id="wave_plus_date_coded"),
        pytest.param("02", "981e", "2018-09-30", id="wave_plus_date_coded_2"),
        pytest.param("02", "9807", "2018-09-07", id="wave_plus_date_coded_3"),
        pytest.param("02", "c803", "2018-12-03", id="wave_plus_date_coded_4"),
        pytest.param("01", "c804", "0.4.3", id="wave_radon_not_date_coded"),
        pytest.param("02", "ffff", None, id="not_reported"),
        pytest.param("02", "0000", None, id="zero"),
        pytest.param("01", "3f00", None, id="zero_with_build_bits"),
    ],
)
def test_wave_plus_msp_version(
    device_type: str, raw_version: str, version: str | None
) -> None:
    """Test the MSP version is decoded from the Wave Plus / Wave Radon self-check."""
    decoded = WaveRadonAndPlusCommandDecode().decode_data(
        _LOGGER, _wave_plus_response(device_type, raw_version)
    )

    assert decoded is not None
    assert decoded[MSP_VERSION] == version


def _wave_mini_response(ble_version: str, sub_version: str) -> bytearray:
    return bytearray.fromhex(
        f"6d0064000000{ble_version}01020304f4015802{sub_version}20038403b80b4cc4b0040000"
    )


@pytest.mark.parametrize(
    ("ble_raw", "sub_raw", "ble_version", "sub_version"),
    [
        pytest.param("00000402", "00020202", "2.4.0", "2.2.2", id="versions_set"),
        pytest.param("ffffffff", "ffffffff", None, None, id="versions_not_set"),
        pytest.param("c8000000", "00000000", None, None, id="zero_versions"),
        pytest.param("00000402", "ffffffff", "2.4.0", None, id="sub_not_set"),
    ],
)
def test_wave_mini_chip_versions(
    ble_raw: str,
    sub_raw: str,
    ble_version: str | None,
    sub_version: str | None,
) -> None:
    """Test the BLE and SUB versions are decoded from the Wave Mini self-check."""
    decoded = WaveMiniCommandDecode().decode_data(
        _LOGGER, _wave_mini_response(ble_raw, sub_raw)
    )

    assert decoded == {
        BATTERY: 3.0,
        BLE_VERSION: ble_version,
        SUB_VERSION: sub_version,
    }


def test_atom_without_response(caplog: pytest.LogCaptureFixture) -> None:
    """Test an Atom request without a response decodes to None."""
    caplog.set_level(logging.DEBUG)
    decoder = AtomCommandDecode(url=AtomRequestPath.LATEST_VALUES)

    assert decoder.decode_data(_LOGGER, None) is None
    assert "No data received" in caplog.text
