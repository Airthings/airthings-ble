import logging
from airthings_ble.wave_enhance.request import (
    WaveEnhanceRequest,
    WaveEnhanceRequestPath,
    WaveEnhanceResponse,
)

_LOGGER = logging.getLogger(__name__)


def test_wave_enhance_request():
    """Test the Wave Enhance request."""
    request = WaveEnhanceRequest(url=WaveEnhanceRequestPath.LATEST_VALUES)
    assert request.url == WaveEnhanceRequestPath.LATEST_VALUES
    assert len(request.random_bytes) == 2


def test_wave_enhance_request_response():
    """Test the Wave Enhance request."""
    request = WaveEnhanceRequest(
        url=WaveEnhanceRequestPath.LATEST_VALUES, random_bytes=bytes.fromhex("E473")
    )

    assert request.as_bytes()[0:2] == bytes.fromhex("0301")
    assert request.as_bytes()[2:4] == request.random_bytes
    assert request.as_bytes()[4:8] == bytes.fromhex("81A1006D")
    assert request.as_bytes()[8:] == request.url.as_bytes()

    response = WaveEnhanceResponse(
        logger=_LOGGER,
        response=bytes.fromhex(
            "1001000345e47381a2006d32393939392f302f333130313202583ea9634e4f49"
            + "182763544d501972f06348554d190d2f63434f321902dc63564f43190115634c5"
            + "55801635052531a005f364663424154190b346354494d1876"
        ),
        random_bytes=request.random_bytes,
        path=WaveEnhanceRequestPath.LATEST_VALUES,
    )

    sensor_data = response.parse()

    assert sensor_data["TMP"] == 29424
    assert sensor_data["HUM"] == 3375
    assert sensor_data["CO2"] == 732
    assert sensor_data["VOC"] == 277
    assert sensor_data["LUX"] == 1
    assert sensor_data["PRS"] == 6239814
    assert sensor_data["BAT"] == 2868
    assert sensor_data["TIM"] == 118
    assert sensor_data["NOI"] == 39
