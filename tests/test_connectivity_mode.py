from airthings_ble.connectivity_type import AirthingsConnectivityType


def test_connectivity_mode() -> None:
    assert AirthingsConnectivityType.from_int(1) == AirthingsConnectivityType.SMARTLINK
    assert AirthingsConnectivityType.from_int(4) == AirthingsConnectivityType.BLE
    assert AirthingsConnectivityType.from_int(0) == AirthingsConnectivityType.UNKNOWN
    assert AirthingsConnectivityType.from_int(99) == AirthingsConnectivityType.UNKNOWN
