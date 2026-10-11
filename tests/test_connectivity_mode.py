import pytest
from airthings_ble.connectivity_mode import AirthingsConnectivityMode


@pytest.mark.parametrize(
    "input_number,expected_mode",
    [
        (1, AirthingsConnectivityMode.SMARTLINK),
        (4, AirthingsConnectivityMode.BLE),
        (0, AirthingsConnectivityMode.NOT_CONFIGURED),
        (2, None),
        (99, None),
    ],
)
def test_connectivity_mode(
    input_number: int, expected_mode: AirthingsConnectivityMode | None
) -> None:
    assert AirthingsConnectivityMode.from_atom_int(input_number) == expected_mode
