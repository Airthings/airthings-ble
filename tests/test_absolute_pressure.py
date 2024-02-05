from airthings_ble.parser import get_absolute_pressure


def test_radon_level():
    assert get_absolute_pressure(elevation=0, data=1000) == 1000
    assert get_absolute_pressure(elevation=100, data=1000) == 1011.94
