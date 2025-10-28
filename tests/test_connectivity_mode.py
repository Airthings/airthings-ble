import pytest
from airthings_ble.connectivity_type import AirthingsConnectivityMode


@pytest.mark.parametrize(
    "input_number,expected_mode",
    [
        (1, AirthingsConnectivityMode.SMARTLINK),
        (4, AirthingsConnectivityMode.BLE),
        (0, AirthingsConnectivityMode.UNKNOWN),
        (99, AirthingsConnectivityMode.UNKNOWN),
    ],
)
def test_connectivity_mode(
    input_number: int, expected_mode: AirthingsConnectivityMode
) -> None:
    assert AirthingsConnectivityMode.from_atom_int(input_number) == expected_mode
