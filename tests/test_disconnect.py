import asyncio
import logging
from typing import Any, Callable

import pytest
from airthings_ble import AirthingsBluetoothDeviceData, DisconnectedError

from fakes import ADDRESS, FakeClient, ble_device, device_info_gatt

_LOGGER = logging.getLogger(__name__)


class _TornDownClient:
    @property
    def address(self) -> str:
        raise AttributeError("'NoneType' object has no attribute 'address'")


class _DisconnectingClient(FakeClient):
    disconnected_callback: Callable[[Any], None]

    async def read_gatt_char(self, characteristic: Any) -> bytearray:
        self.disconnected_callback(_TornDownClient())
        await asyncio.Event().wait()
        raise AssertionError("unreachable")


@pytest.mark.asyncio
async def test_disconnect_callback_does_not_read_client_address(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Test a disconnect reported after the client backend is gone ends the update."""
    client = _DisconnectingClient(device_info_gatt("2930", "G-BLE-1.5.3-master+0"))

    async def fake_establish_connection(*args: Any, **kwargs: Any) -> FakeClient:
        client.disconnected_callback = kwargs["disconnected_callback"]
        return client

    monkeypatch.setattr(
        "airthings_ble.parser.establish_connection", fake_establish_connection
    )
    data = AirthingsBluetoothDeviceData(logger=_LOGGER)

    with caplog.at_level(logging.DEBUG), pytest.raises(DisconnectedError):
        await data.update_device(ble_device())

    assert f"Disconnected from {ADDRESS}" in caplog.text
