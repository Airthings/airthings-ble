from logging import Logger

import pytest
from airthings_ble import AirthingsBluetoothDeviceData
from airthings_ble.parser import AirthingsDevice


@pytest.mark.parametrize(
    "is_metric,expected_radon_values",
    [
        (True, [0, 100, 200, 300]),
        (False, [0, 2.7, 5.4, 8.1]),
    ],
)
def test_corentium_home_2_sensor_data(
    is_metric: bool,
    expected_radon_values: list[float],
) -> None:
    """Test Corentium Home 2 sensor data parsing."""
    device = AirthingsBluetoothDeviceData(
        logger=Logger("test_logger"),
        is_metric=is_metric,
    )
    sensors: dict[str, str | float | None] = {}

    device._parse_sensor_data(
        device=AirthingsDevice(),
        sensors=sensors,
        sensor_data={
            "R24": 0.0,
            "R7D": 100.0,
            "R30D": 200.0,
            "R1Y": 300,
        },
    )

    assert sensors["radon_1day_avg"] == expected_radon_values[0]
    assert sensors["radon_week_avg"] == expected_radon_values[1]
    assert sensors["radon_month_avg"] == expected_radon_values[2]
    assert sensors["radon_year_avg"] == expected_radon_values[3]
