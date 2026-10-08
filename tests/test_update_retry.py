import logging

import pytest
from airthings_ble import AirthingsBluetoothDeviceData

from fakes import FakeClient, ble_device, device_info_gatt, use_clients

_LOGGER = logging.getLogger(__name__)
_WAVE_PLUS = device_info_gatt("2930", "G-BLE-1.5.3-master+0")


@pytest.mark.asyncio
async def test_timed_out_update_is_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test an update that times out is retried and the next attempt is used."""
    monkeypatch.setattr("airthings_ble.parser.UPDATE_TIMEOUT", 0.01)
    slow = FakeClient(_WAVE_PLUS, read_delay=1)
    use_clients(monkeypatch, slow, FakeClient(_WAVE_PLUS))
    data = AirthingsBluetoothDeviceData(logger=_LOGGER, max_attempts=2)

    device = await data.update_device(ble_device())

    assert device.sw_version == "G-BLE-1.5.3-master+0"
    assert slow.disconnected


@pytest.mark.asyncio
async def test_timed_out_final_attempt_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a timeout on the final attempt is raised."""
    monkeypatch.setattr("airthings_ble.parser.UPDATE_TIMEOUT", 0.01)
    use_clients(
        monkeypatch,
        FakeClient(_WAVE_PLUS, read_delay=1),
        FakeClient(_WAVE_PLUS, read_delay=1),
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER, max_attempts=2)

    with pytest.raises(TimeoutError):
        await data.update_device(ble_device())


@pytest.mark.asyncio
async def test_timed_out_update_is_retried_only_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test a second timeout is raised even when attempts remain."""
    monkeypatch.setattr("airthings_ble.parser.UPDATE_TIMEOUT", 0.01)
    unused = FakeClient(_WAVE_PLUS)
    use_clients(
        monkeypatch,
        FakeClient(_WAVE_PLUS, read_delay=1),
        FakeClient(_WAVE_PLUS, read_delay=1),
        unused,
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER, max_attempts=5)

    with pytest.raises(TimeoutError):
        await data.update_device(ble_device())

    assert not unused.disconnected
