"""Airthings radon level definitions and utilities."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AirthingsRadonLevel:
    """Airthings radon level definition."""

    min_value: Optional[float]
    max_value: Optional[float]
    name: str


LEVELS = [
    # No action necessary
    AirthingsRadonLevel(0, 100, "good"),
    # Experiment with ventilation and sealing cracks
    AirthingsRadonLevel(100, 150, "fair"),
    # Contact a professional radon mitigator
    AirthingsRadonLevel(150, None, "poor"),
]


def _in_range(value: float, min_value: float | None, max_value: float | None) -> bool:
    """Check if value is in range [min_value, max_value)."""
    return (min_value is None or value >= min_value) and (
        max_value is None or value < max_value
    )


def get_radon_level(value: float) -> str:
    """Get radon level string based on value."""
    for level in LEVELS:
        if _in_range(value, level.min_value, level.max_value):
            return level.name
    return "unknown"
