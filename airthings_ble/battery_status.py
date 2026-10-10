"""Airthings battery status."""

from enum import Enum


class AirthingsBatteryStatus(str, Enum):
    """Airthings battery status advertised by the Wave Plus and Wave Radon."""

    FULL = "full"
    LOW = "low"
    LIMITED = "limited"
    STOPPED = "stopped"
