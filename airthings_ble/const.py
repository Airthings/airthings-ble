"""Constants for Airthings BLE parser"""

from uuid import UUID

MFCT_ID = 820

UPDATE_TIMEOUT = 15

# Use full UUID since we do not use UUID from bluetooth library
CHAR_UUID_MANUFACTURER_NAME = UUID("00002a29-0000-1000-8000-00805f9b34fb")
CHAR_UUID_SERIAL_NUMBER_STRING = UUID("00002a25-0000-1000-8000-00805f9b34fb")
CHAR_UUID_MODEL_NUMBER_STRING = UUID("00002a24-0000-1000-8000-00805f9b34fb")
CHAR_UUID_DEVICE_NAME = UUID("00002a00-0000-1000-8000-00805f9b34fb")
CHAR_UUID_FIRMWARE_REV = UUID("00002a26-0000-1000-8000-00805f9b34fb")
CHAR_UUID_HARDWARE_REV = UUID("00002a27-0000-1000-8000-00805f9b34fb")

CHAR_UUID_DATETIME = UUID("00002a08-0000-1000-8000-00805f9b34fb")
CHAR_UUID_TEMPERATURE = UUID("00002a6e-0000-1000-8000-00805f9b34fb")
CHAR_UUID_HUMIDITY = UUID("00002a6f-0000-1000-8000-00805f9b34fb")
CHAR_UUID_RADON_1DAYAVG = UUID("b42e01aa-ade7-11e4-89d3-123b93f75cba")
CHAR_UUID_RADON_LONG_TERM_AVG = UUID("b42e0a4c-ade7-11e4-89d3-123b93f75cba")
CHAR_UUID_ILLUMINANCE_ACCELEROMETER = UUID("b42e1348-ade7-11e4-89d3-123b93f75cba")
CHAR_UUID_WAVE_PLUS_DATA = UUID("b42e2a68-ade7-11e4-89d3-123b93f75cba")
CHAR_UUID_WAVE_2_DATA = UUID("b42e4dcc-ade7-11e4-89d3-123b93f75cba")
CHAR_UUID_WAVEMINI_DATA = UUID("b42e3b98-ade7-11e4-89d3-123b93f75cba")

COMMAND_UUID_WAVE_2 = UUID("b42e50d8-ade7-11e4-89d3-123b93f75cba")
COMMAND_UUID_WAVE_PLUS = UUID("b42e2d06-ade7-11e4-89d3-123b93f75cba")
COMMAND_UUID_WAVE_MINI = UUID("b42e3ef4-ade7-11e4-89d3-123b93f75cba")

"""
0 - 49 Bq/m3  (0 - 1.3 pCi/L):
No action necessary.
50 - 99 Bq/m3 (1.4 - 2.6 pCi/L):
Experiment with ventilation and sealing cracks to reduce levels.
100 Bq/m3 - 299 Bq/m3 (2.7 - 8 pCi/L):
Keep measuring. If levels are maintained for more than 3 months,
contact a professional radon mitigator.
300 Bq/m3 (8.1 pCi/L) and up:
Keep measuring. If levels are maintained for more than 1 month,
contact a professional radon mitigator.
"""
RADON_VERY_LOW = (0, 49, "very low")
RADON_LOW = (50, 99, "low")
RADON_MODERATE = (100, 299, "moderate")
RADON_HIGH = (300, None, "high")

"""
0 - 249 ppb
The VOC contents in the air are low.
250 - 1999 ppb
Look for VOC sources if this average level persists for a month
2000 ppb and up
The VOC contents are very high - consider taking action/ventilating right now
"""
VOC_LOW = (0, 249, "low")
VOC_MODERATE = (250, 1999, "moderate")
VOC_VERY_HIGH = (2000, None, "very high")

"""
250 - 399 ppm
Normal background concentration in outdoor ambient air
400 - 999 ppm
Concentrations typical of occupied indoor spaces with good air exchange.
1000 - 1999 ppm
Complaints of drowsiness and poor air
2000 - 4999 ppm
Headaches, sleepiness and stagnant, stale, stuffy air. Poor concentration, loss
of attention, increased heart rate and slight nausea.
5000 - 39999 ppm
Extremely high
40000 and up
Exposure may lead to serious oxygen deprivation resulting in permanent brain
damage, coma and even death.
"""
CO2_LOW = (0, 249, "low")
CO2_OUTDOOR_NORMAL = (250, 399, "outdoor normal")
CO2_INDOOR_NORMAL = (400, 999, "indoor normal")
CO2_HIGH = (1000, 1999, "high")
CO2_VERY_HIGH = (2000, 4999, "very high")
CO2_EXTREMELLY_HIGH = (5000, 39999, "extremelly high")
CO2_CRITICAL = (40000, None, "critical")

BQ_TO_PCI_MULTIPLIER = 0.027

CO2_MAX = 65534
VOC_MAX = 65534
PERCENTAGE_MAX = 100
PRESSURE_MAX = 1310
RADON_MAX = 16383
TEMPERATURE_MAX = 100

DEFAULT_MAX_UPDATE_ATTEMPTS = 1
