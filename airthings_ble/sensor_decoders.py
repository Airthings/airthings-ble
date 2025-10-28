""""Sensor data decoders for Airthings BLE devices."""

import struct
from datetime import datetime
from typing import Callable, Optional, Tuple

from .const import (
    CHAR_UUID_DATETIME,
    CHAR_UUID_HUMIDITY,
    CHAR_UUID_ILLUMINANCE_ACCELEROMETER,
    CHAR_UUID_RADON_1DAYAVG,
    CHAR_UUID_RADON_LONG_TERM_AVG,
    CHAR_UUID_TEMPERATURE,
    CHAR_UUID_WAVE_2_DATA,
    CHAR_UUID_WAVE_PLUS_DATA,
    CHAR_UUID_WAVEMINI_DATA,
    CO2_MAX,
    PERCENTAGE_MAX,
    PRESSURE_MAX,
    RADON_MAX,
    TEMPERATURE_MAX,
    VOC_MAX,
)


def _decode_base(
    name: str, format_type: str, scale: float
) -> Callable[[bytearray], dict[str, Tuple[float, ...]]]:
    def handler(raw_data: bytearray) -> dict[str, Tuple[float, ...]]:
        val = struct.unpack(format_type, raw_data)
        if len(val) == 1:
            res = val[0] * scale
        else:
            res = val
        return {name: res}

    return handler


def _decode_attr(
    name: str, format_type: str, scale: float, max_value: Optional[float] = None
) -> Callable[[bytearray], dict[str, float | None | str]]:
    """same as base decoder, but expects only one value.. for real"""

    def handler(raw_data: bytearray) -> dict[str, float | None | str]:
        val = struct.unpack(format_type, raw_data)
        res: float | None = None
        if len(val) == 1:
            res = val[0] * scale
        if res is not None and max_value is not None:
            # Verify that the result is not above the maximum allowed value
            if res > max_value:
                res = None
        data: dict[str, float | None | str] = {name: res}
        return data

    return handler


def _decode_wave_plus(
    name: str, format_type: str, scale: float
) -> Callable[[bytearray], dict[str, float | None | str]]:
    def handler(raw_data: bytearray) -> dict[str, float | None | str]:
        vals = _decode_base(name, format_type, scale)(raw_data)
        val = vals[name]
        data: dict[str, float | None | str] = {}
        data["date_time"] = str(datetime.isoformat(datetime.now()))
        data["humidity"] = validate_value(value=val[1] / 2.0, max_value=PERCENTAGE_MAX)
        data["illuminance"] = illuminance_converter(value=val[2])
        data["radon_1day_avg"] = validate_value(value=val[4], max_value=RADON_MAX)
        data["radon_longterm_avg"] = validate_value(value=val[5], max_value=RADON_MAX)
        data["temperature"] = validate_value(
            value=val[6] / 100.0, max_value=TEMPERATURE_MAX
        )
        data["pressure"] = validate_value(val[7] / 50.0, max_value=PRESSURE_MAX)
        data["co2"] = validate_value(value=val[8] * 1.0, max_value=CO2_MAX)
        data["voc"] = validate_value(value=val[9] * 1.0, max_value=VOC_MAX)
        return data

    return handler


def _decode_wave_radon(
    name: str, format_type: str, scale: float
) -> Callable[[bytearray], dict[str, float | None | str]]:
    def handler(raw_data: bytearray) -> dict[str, float | None | str]:
        vals = _decode_base(name, format_type, scale)(raw_data)
        val = vals[name]
        data: dict[str, float | None | str] = {}
        data["date_time"] = str(datetime.isoformat(datetime.now()))
        data["illuminance"] = illuminance_converter(value=val[2])
        data["humidity"] = validate_value(value=val[1] / 2.0, max_value=PERCENTAGE_MAX)
        data["radon_1day_avg"] = validate_value(value=val[4], max_value=RADON_MAX)
        data["radon_longterm_avg"] = validate_value(value=val[5], max_value=RADON_MAX)
        data["temperature"] = validate_value(
            value=val[6] / 100.0, max_value=TEMPERATURE_MAX
        )
        return data

    return handler


def _decode_wave_mini(
    name: str, format_type: str, scale: float
) -> Callable[[bytearray], dict[str, float | None | str]]:
    def handler(raw_data: bytearray) -> dict[str, float | None | str]:
        vals = _decode_base(name, format_type, scale)(raw_data)
        val = vals[name]
        data: dict[str, float | None | str] = {}
        data["date_time"] = str(datetime.isoformat(datetime.now()))
        data["temperature"] = validate_value(
            value=round(val[2] / 100.0 - 273.15, 2), max_value=TEMPERATURE_MAX
        )
        data["pressure"] = float(val[3] / 50.0)
        data["humidity"] = validate_value(
            value=val[4] / 100.0, max_value=PERCENTAGE_MAX
        )
        data["voc"] = validate_value(value=val[5] * 1.0, max_value=VOC_MAX)
        return data

    return handler


def _decode_wave(
    name: str, format_type: str, scale: float
) -> Callable[[bytearray], dict[str, float | None | str]]:
    def handler(raw_data: bytearray) -> dict[str, float | None | str]:
        vals = _decode_base(name, format_type, scale)(raw_data)
        val = vals[name]
        data: dict[str, float | None | str] = {
            name: str(
                datetime(
                    int(val[0]),
                    int(val[1]),
                    int(val[2]),
                    int(val[3]),
                    int(val[4]),
                    int(val[5]),
                ).isoformat()
            )
        }
        return data

    return handler


def _decode_wave_illum_accel(
    name: str, format_type: str, scale: float
) -> Callable[[bytearray], dict[str, float | None | str]]:
    def handler(raw_data: bytearray) -> dict[str, float | None | str]:
        vals = _decode_base(name, format_type, scale)(raw_data)
        val = vals[name]
        data: dict[str, float | None | str] = {}
        data["illuminance"] = illuminance_converter(val[0] * scale)
        data["accelerometer"] = str(val[1] * scale)
        return data

    return handler


def validate_value(value: float, max_value: float) -> Optional[float]:
    """Validate if the given 'value' is within the specified range [min, max]"""
    min_value = 0
    if min_value <= value <= max_value:
        return value
    return None


def illuminance_converter(value: float) -> Optional[int]:
    """Convert illuminance from a 8-bit value to percentage."""
    if (validated := validate_value(value, max_value=255)) is not None:
        return int(validated / 255 * PERCENTAGE_MAX)
    return None


SENSOR_DECODERS: dict[
    str,
    Callable[[bytearray], dict[str, float | None | str]],
] = {
    str(CHAR_UUID_DATETIME): _decode_wave(name="date_time", format_type="H5B", scale=0),
    str(CHAR_UUID_HUMIDITY): _decode_attr(
        name="humidity",
        format_type="H",
        scale=1.0 / 100.0,
        max_value=PERCENTAGE_MAX,
    ),
    str(CHAR_UUID_RADON_1DAYAVG): _decode_attr(
        name="radon_1day_avg", format_type="H", scale=1.0
    ),
    str(CHAR_UUID_RADON_LONG_TERM_AVG): _decode_attr(
        name="radon_longterm_avg", format_type="H", scale=1.0
    ),
    str(CHAR_UUID_ILLUMINANCE_ACCELEROMETER): _decode_wave_illum_accel(
        name="illuminance_accelerometer", format_type="BB", scale=1.0
    ),
    str(CHAR_UUID_TEMPERATURE): _decode_attr(
        name="temperature", format_type="h", scale=1.0 / 100.0
    ),
    str(CHAR_UUID_WAVE_2_DATA): _decode_wave_radon(
        name="Wave2", format_type="<4B8H", scale=1.0
    ),
    str(CHAR_UUID_WAVE_PLUS_DATA): _decode_wave_plus(
        name="Plus", format_type="<4B8H", scale=0
    ),
    str(CHAR_UUID_WAVEMINI_DATA): _decode_wave_mini(
        name="WaveMini", format_type="<2B5HLL", scale=1.0
    ),
}
