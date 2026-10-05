import logging
from typing import Any

import pytest
from airthings_ble import AirthingsBluetoothDeviceData, AirthingsDeviceType
from airthings_ble.const import COMMAND_UUID_ATOM

from fakes import (
    FakeClient,
    FakeService,
    atom_service,
    ble_device,
    device_info_gatt,
    use_clients,
)

_LOGGER = logging.getLogger(__name__)

_CORENTIUM_HOME_2_LATEST_VALUES = {
    "R24": 3,
    "R7D": 7,
    "R30": 120,
    "R1Y": 180,
    "TMP": 29655,
    "HUM": 3468,
    "BAT": 2945,
    "TIM": 1565,
}
_WAVE_ENHANCE_LATEST_VALUES = {
    "NOI": 39,
    "TMP": 29424,
    "HUM": 3375,
    "CO2": 732,
    "VOC": 277,
    "LUX": 1,
    "PRS": 6239814,
    "BAT": 2868,
    "TIM": 118,
}
_WAVE_ENHANCE_SENSORS = {
    "connectivity_mode": "Bluetooth",
    "battery": 87,
    "lux": 1,
    "co2": 732,
    "voc": 277,
    "humidity": 33.75,
    "temperature": 21.09,
    "noise": 39,
    "pressure": 974.9709375,
}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("model", "device_type"),
    [
        ("3210", AirthingsDeviceType.WAVE_ENHANCE_EU),
        ("3220", AirthingsDeviceType.WAVE_ENHANCE_US),
    ],
)
async def test_wave_enhance_update(
    monkeypatch: pytest.MonkeyPatch, model: str, device_type: AirthingsDeviceType
) -> None:
    """Test a Wave Enhance reports its latest values and connectivity mode."""
    use_clients(
        monkeypatch,
        FakeClient(
            device_info_gatt(model, "T-SUB-3.0.3-master+0"),
            [atom_service()],
            atom_latest_values=_WAVE_ENHANCE_LATEST_VALUES,
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert device.model == device_type
    assert device.friendly_name() == "Airthings Wave Enhance"
    assert device.firmware.need_firmware_upgrade is False
    assert device.sensors == _WAVE_ENHANCE_SENSORS


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("is_metric", "radon"),
    [
        (True, (3, 7, 120, 180)),
        (False, (3 * 0.027, 7 * 0.027, 120 * 0.027, 180 * 0.027)),
    ],
)
async def test_corentium_home_2_update(
    monkeypatch: pytest.MonkeyPatch, is_metric: bool, radon: tuple[float, ...]
) -> None:
    """Test a Corentium Home 2 reports every radon average with a Bq/m3 level."""
    use_clients(
        monkeypatch,
        FakeClient(
            device_info_gatt("3250", "R-SUB-1.3.5-master+0"),
            [atom_service()],
            atom_latest_values=_CORENTIUM_HOME_2_LATEST_VALUES,
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER, is_metric=is_metric)

    device = await data.update_device(ble_device())

    assert device.model == AirthingsDeviceType.CORENTIUM_HOME_2
    assert device.friendly_name() == "Airthings Corentium Home 2"
    assert device.sensors == {
        "connectivity_mode": "Bluetooth",
        "battery": 95,
        "humidity": 34.68,
        "temperature": 23.4,
        "radon_1day_avg": pytest.approx(radon[0]),
        "radon_1day_level": "good",
        "radon_week_avg": pytest.approx(radon[1]),
        "radon_week_level": "good",
        "radon_month_avg": pytest.approx(radon[2]),
        "radon_month_level": "fair",
        "radon_year_avg": pytest.approx(radon[3]),
        "radon_year_level": "poor",
    }


@pytest.mark.asyncio
async def test_invalid_connectivity_mode_keeps_latest_values(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Test an unparseable connectivity mode still reports the latest values."""
    use_clients(
        monkeypatch,
        FakeClient(
            device_info_gatt("3220", "T-SUB-3.0.3-master+0"),
            [atom_service()],
            atom_latest_values=_WAVE_ENHANCE_LATEST_VALUES,
            atom_connectivity_mode="Bluetooth",
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert "Failed to decode command response" in caplog.text
    assert device.sensors == {
        key: value
        for key, value in _WAVE_ENHANCE_SENSORS.items()
        if key != "connectivity_mode"
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("latest_values", [[1, 2], 7])
async def test_invalid_latest_values_keep_connectivity_mode(
    monkeypatch: pytest.MonkeyPatch, latest_values: Any
) -> None:
    """Test latest values that are not a map give no sensor readings."""
    use_clients(
        monkeypatch,
        FakeClient(
            device_info_gatt("3220", "T-SUB-3.0.3-master+0"),
            [atom_service()],
            atom_latest_values=latest_values,
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert device.sensors == {"connectivity_mode": "Bluetooth"}


@pytest.mark.asyncio
@pytest.mark.command_timeout
async def test_atom_command_timeout(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Test unanswered Atom requests give an empty reading instead of failing."""
    monkeypatch.setattr("airthings_ble.parser.COMMAND_TIMEOUT", 0.01)
    client = FakeClient(
        device_info_gatt("3220", "T-SUB-3.0.3-master+0"),
        [atom_service()],
        silent_commands=True,
    )
    use_clients(monkeypatch, client)
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert "Timeout getting command data" in caplog.text
    assert device.sensors == {}
    assert not client.notifying


@pytest.mark.asyncio
async def test_atom_device_without_notify_characteristic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test an Atom device missing the notify characteristic is not queried."""
    use_clients(
        monkeypatch,
        FakeClient(
            device_info_gatt("3220", "T-SUB-3.0.3-master+0"),
            [FakeService([COMMAND_UUID_ATOM])],
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert device.sensors == {}


@pytest.mark.asyncio
async def test_atom_readings_absent_from_latest_values_are_not_reported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test only the readings present in the latest values are reported."""
    use_clients(
        monkeypatch,
        FakeClient(
            device_info_gatt("3250", "R-SUB-1.3.5-master+0"),
            [atom_service()],
            atom_latest_values={"R24": 50, "TIM": 1565},
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    assert device.sensors == {
        "connectivity_mode": "Bluetooth",
        "radon_1day_avg": 50.0,
        "radon_1day_level": "good",
    }


@pytest.mark.asyncio
async def test_corentium_home_2_zero_radon(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test radon averages of zero are reported, not dropped."""
    use_clients(
        monkeypatch,
        FakeClient(
            device_info_gatt("3250", "R-SUB-1.3.5-master+0"),
            [atom_service()],
            atom_latest_values={
                **_CORENTIUM_HOME_2_LATEST_VALUES,
                "R24": 0,
                "R7D": 0,
                "R30": 0,
                "R1Y": 0,
            },
        ),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    device = await data.update_device(ble_device())

    for period in ("1day", "week", "month", "year"):
        assert device.sensors[f"radon_{period}_avg"] == 0
        assert device.sensors[f"radon_{period}_level"] == "good"
