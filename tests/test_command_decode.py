import logging

import pytest
from airthings_ble.command_decode import (
    CommandDecode,
    WaveMiniCommandDecode,
    WaveRadonAndPlusCommandDecode,
)

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
