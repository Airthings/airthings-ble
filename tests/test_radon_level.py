from airthings_ble.radon_level import get_radon_level


def test_radon_level() -> None:
    assert get_radon_level(0) == "good"
    assert get_radon_level(50) == "good"
    assert get_radon_level(99.9) == "good"

    assert get_radon_level(100) == "fair"
    assert get_radon_level(149) == "fair"

    assert get_radon_level(150) == "poor"
    assert get_radon_level(300) == "poor"
    assert get_radon_level(1000) == "poor"

    assert get_radon_level(-10) == "unknown"
