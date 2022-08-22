"""Constants for Airthings BLE parser"""

from uuid import UUID

MFCT_ID = 820


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
CHAR_UUID_ILLUMINANCE_ACCELEROMETER = UUID(
    "b42e1348-ade7-11e4-89d3-123b93f75cba"
)
CHAR_UUID_WAVE_PLUS_DATA = UUID("b42e2a68-ade7-11e4-89d3-123b93f75cba")
CHAR_UUID_WAVE_2_DATA = UUID("b42e4dcc-ade7-11e4-89d3-123b93f75cba")
CHAR_UUID_WAVEMINI_DATA = UUID("b42e3b98-ade7-11e4-89d3-123b93f75cba")
COMMAND_UUID = UUID(
    "b42e2d06-ade7-11e4-89d3-123b93f75cba"
)  # "Access Control Point" Characteristic

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
VERY_LOW = (0, 49, "very low")
LOW = (50, 99, "low")
MODERATE = (100, 299, "moderate")
HIGH = (300, None, "high")

BQ_TO_PCI_MULTIPLIER = 0.027
