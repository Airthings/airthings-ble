from airthings_ble.parser import get_radon_level


def test_radon_level() -> None:
    assert get_radon_level(0) == "very low"
    assert get_radon_level(49) == "very low"
    assert get_radon_level(50) == "low"
    assert get_radon_level(99) == "low"
    assert get_radon_level(100) == "moderate"
    assert get_radon_level(299) == "moderate"
    assert get_radon_level(300) == "high"
    assert get_radon_level(1000) == "high"
