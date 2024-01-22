from enum import Enum


class AirthingsDeviceType(Enum):
    WAVE_GEN_1 = "2900"
    WAVE_MINI = "2920"
    WAVE_PLUS = "2930"
    WAVE_RADON = "2950"

    @classmethod
    def product_name(self):
        if self == AirthingsDeviceType.WAVE_GEN_1:
            return "Wave Gen 1"
        elif self == AirthingsDeviceType.WAVE_MINI:
            return "Wave Mini"
        elif self == AirthingsDeviceType.WAVE_PLUS:
            return "Wave Plus"
        elif self == AirthingsDeviceType.WAVE_RADON:
            return "Wave Radon"
        else:
            return "Unknown"

