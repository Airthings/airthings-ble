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

    @classmethod
    def battery_percentage(self, vin) -> int:
        if self == AirthingsDeviceType.WAVE_MINI:
            # The only device that has a different battery voltage range (3 x AAA)
            if vin >= 4.50:
                return 100
            elif 4.20 <= vin < 4.50:
                return int((vin - 4.20) / (4.50 - 4.20) * (100 - 85) + 85)
            elif 3.90 <= vin < 4.20:
                return int((vin - 3.90) / (4.20 - 3.90) * (85 - 62) + 62)
            elif 3.75 <= vin < 3.90:
                return int((vin - 3.75) / (3.90 - 3.75) * (62 - 42) + 42)
            elif 3.30 <= vin < 3.75:
                return int((vin - 3.30) / (3.75 - 3.30) * (42 - 23) + 23)
            elif 2.40 <= vin < 3.30:
                return int((vin - 2.40) / (3.30 - 2.40) * (23 - 0) + 0)
            return 0
        else:
            # All other devices (2 x AA)
            if vin >= 3.00:
                return 100
            elif 2.80 <= vin < 3.00:
                return int((vin - 2.80) / (3.00 - 2.80) * (100 - 81) + 81)
            elif 2.60 <= vin < 2.80:
                return int((vin - 2.60) / (2.80 - 2.60) * (81 - 53) + 53)
            elif 2.50 <= vin < 2.60:
                return int((vin - 2.50) / (2.60 - 2.50) * (53 - 28) + 28)
            elif 2.20 <= vin < 2.50:
                return int((vin - 2.20) / (2.50 - 2.20) * (28 - 5) + 5)
            elif 2.10 <= vin < 2.20:
                return int((vin - 2.10) / (2.20 - 2.10) * (5 - 0) + 0)
            else:
                return 0
