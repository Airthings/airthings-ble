"""Parser for Airthings BLE devices"""

from __future__ import annotations

import asyncio
import struct
from collections import namedtuple
from datetime import datetime
from logging import Logger
from math import exp
from typing import Tuple

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection

from .const import (
    BQ_TO_PCI_MULTIPLIER,
    CHAR_UUID_DATETIME,
    CHAR_UUID_DEVICE_NAME,
    CHAR_UUID_FIRMWARE_REV,
    CHAR_UUID_HARDWARE_REV,
    CHAR_UUID_HUMIDITY,
    CHAR_UUID_ILLUMINANCE_ACCELEROMETER,
    CHAR_UUID_MANUFACTURER_NAME,
    CHAR_UUID_MODEL_NUMBER_STRING,
    CHAR_UUID_RADON_1DAYAVG,
    CHAR_UUID_RADON_LONG_TERM_AVG,
    CHAR_UUID_SERIAL_NUMBER_STRING,
    CHAR_UUID_TEMPERATURE,
    CHAR_UUID_WAVE_2_DATA,
    CHAR_UUID_WAVE_PLUS_DATA,
    CHAR_UUID_WAVEMINI_DATA,
    COMMAND_UUID,
    HIGH,
    LOW,
    MODERATE,
    VERY_LOW,
)

Characteristic = namedtuple("Characteristic", ["uuid", "name", "format"])

manufacturer_characteristics = Characteristic(
    CHAR_UUID_MANUFACTURER_NAME, "manufacturer", "utf-8"
)
device_info_characteristics = [
    manufacturer_characteristics,
    Characteristic(CHAR_UUID_SERIAL_NUMBER_STRING, "serial_nr", "utf-8"),
    Characteristic(CHAR_UUID_MODEL_NUMBER_STRING, "model_nr", "utf-8"),
    Characteristic(CHAR_UUID_DEVICE_NAME, "device_name", "utf-8"),
    Characteristic(CHAR_UUID_FIRMWARE_REV, "firmware_rev", "utf-8"),
    Characteristic(CHAR_UUID_HARDWARE_REV, "hardware_rev", "utf-8"),
]

sensors_characteristics_uuid = [
    CHAR_UUID_DATETIME,
    CHAR_UUID_TEMPERATURE,
    CHAR_UUID_HUMIDITY,
    CHAR_UUID_RADON_1DAYAVG,
    CHAR_UUID_RADON_LONG_TERM_AVG,
    CHAR_UUID_ILLUMINANCE_ACCELEROMETER,
    CHAR_UUID_WAVE_PLUS_DATA,
    CHAR_UUID_WAVE_2_DATA,
    CHAR_UUID_WAVEMINI_DATA,
    COMMAND_UUID,
]
sensors_characteristics_uuid_str = [
    str(x) for x in sensors_characteristics_uuid
]

# pylint: disable=too-few-public-methods
class BaseDecode:
    """Base class for decoding sensordata"""

    def __init__(self, name, format_type, scale) -> None:
        self.name = name
        self.format_type = format_type
        self.scale = scale

    def decode_data(self, raw_data) -> dict[str, int]:
        """Base decoder"""
        val = struct.unpack(self.format_type, raw_data)
        if len(val) == 1:
            res = val[0] * self.scale
        else:
            res = val
        return {self.name: res}


# pylint: disable=too-few-public-methods
class WavePlussDecode(BaseDecode):
    """Decoder for Wave Plus devices"""

    def decode_data(self, raw_data):
        val = super().decode_data(raw_data)
        val = val[self.name]
        data = {}
        data["date_time"] = str(datetime.isoformat(datetime.now()))
        data["humidity"] = val[1] / 2.0
        data["radon_1day_avg"] = val[4] if 0 <= val[4] <= 16383 else None
        data["radon_longterm_avg"] = val[5] if 0 <= val[5] <= 16383 else None
        data["temperature"] = val[6] / 100.0
        data["rel_atm_pressure"] = val[7] / 50.0
        data["co2"] = val[8] * 1.0
        data["voc"] = val[9] * 1.0
        return data


# pylint: disable=too-few-public-methods
class Wave2Decode(BaseDecode):
    """Decoder for Wave 2 devices"""

    def decode_data(self, raw_data):
        val = super().decode_data(raw_data)
        val = val[self.name]
        data = {}
        data["date_time"] = str(datetime.isoformat(datetime.now()))
        data["humidity"] = val[1] / 2.0
        data["radon_1day_avg"] = val[4] if 0 <= val[4] <= 16383 else None
        data["radon_longterm_avg"] = val[5] if 0 <= val[5] <= 16383 else None
        data["temperature"] = val[6] / 100.0
        return data


# pylint: disable=too-few-public-methods
class WaveMiniDecode(BaseDecode):
    """Decoder for Wave mini devices"""

    def decode_data(self, raw_data):
        val = super().decode_data(raw_data)
        val = val[self.name]
        data = {}
        data["date_time"] = str(datetime.isoformat(datetime.now()))
        data["temperature"] = round(val[1] / 100.0 - 273.15, 2)
        data["humidity"] = val[3] / 100.0
        data["voc"] = val[4] * 1.0
        return data


# pylint: disable=too-few-public-methods
class WaveDecodeDate(BaseDecode):
    """Decoder for just Wave"""

    def decode_data(self, raw_data):
        val = super().decode_data(raw_data)[self.name]
        data = {
            self.name: str(
                datetime(
                    val[0], val[1], val[2], val[3], val[4], val[5]
                ).isoformat()
            )
        }
        return data


# pylint: disable=too-few-public-methods
class WaveDecodeIluminAccel(BaseDecode):
    """Decoder for illuminance and accelerometer"""

    def decode_data(self, raw_data):
        val = super().decode_data(raw_data)[self.name]
        data = {}
        data["illuminance"] = str(val[0] * self.scale)
        data["accelerometer"] = str(val[1] * self.scale)
        return data


# pylint: disable=too-few-public-methods
class CommandDecode:
    """Decoder for the command response"""

    def __init__(self, name, format_type, cmd):
        self.name = name
        self.format_type = format_type
        self.cmd = cmd

    def decode_data(self, raw_data):
        """Decoder returns dict with illuminance and battery"""
        if raw_data is None:
            return {}
        cmd = raw_data[0:1]
        if cmd != self.cmd:
            # _LOGGER.warning("Result for Wrong command received,
            # expected {} got {}".format(self.cmd.hex(), cmd.hex()))
            return {}

        if len(raw_data[2:]) != struct.calcsize(self.format_type):
            # _LOGGER.debug("Wrong length data received ({}) verses
            # expected ({})".format(len(cmd),
            # struct.calcsize(self.format_type)))
            return {}
        val = struct.unpack(self.format_type, raw_data[2:])
        res = {}
        res["illuminance"] = val[2]
        # res['measurement_periods'] =  val[5]
        res["battery"] = val[17] / 1000.0

        return res


def get_radon_level(data) -> str:
    """Returns the applicable radon level"""
    if float(data) <= VERY_LOW[1]:
        radon_level = VERY_LOW[2]
    elif float(data) <= LOW[1]:
        radon_level = LOW[2]
    elif float(data) <= MODERATE[1]:
        radon_level = MODERATE[2]
    else:
        radon_level = HIGH[2]
    return radon_level


# pylint: disable=invalid-name
def get_absolute_pressure(elevation: int, data) -> int:
    """Returns an absolute pressure calculated from the given elevation"""
    p0 = 101325  # Pa
    g = 9.80665  # m/s^2
    M = 0.02896968  # kg/mol
    T0 = 288.16  # K
    R0 = 8.314462618  # J/(mol K)
    h = elevation  # m
    offset = (p0 - (p0 * exp(-g * h * M / (T0 * R0)))) / 100.0  # mbar
    return data + round(offset, 2)


sensor_decoders: dict[str, BaseDecode] = {
    str(CHAR_UUID_WAVE_PLUS_DATA): WavePlussDecode(
        name="Pluss", format_type="BBBBHHHHHHHH", scale=0
    ),
    str(CHAR_UUID_DATETIME): WaveDecodeDate(
        name="date_time", format_type="HBBBBB", scale=0
    ),
    str(CHAR_UUID_HUMIDITY): BaseDecode(
        name="humidity", format_type="H", scale=1.0 / 100.0
    ),
    str(CHAR_UUID_RADON_1DAYAVG): BaseDecode(
        name="radon_1day_avg", format_type="H", scale=1.0
    ),
    str(CHAR_UUID_RADON_LONG_TERM_AVG): BaseDecode(
        name="radon_longterm_avg", format_type="H", scale=1.0
    ),
    str(CHAR_UUID_ILLUMINANCE_ACCELEROMETER): WaveDecodeIluminAccel(
        name="illuminance_accelerometer", format_type="BB", scale=1.0
    ),
    str(CHAR_UUID_TEMPERATURE): BaseDecode(
        name="temperature", format_type="h", scale=1.0 / 100.0
    ),
    str(CHAR_UUID_WAVE_2_DATA): Wave2Decode(
        name="Wave2", format_type="<4B8H", scale=1.0
    ),
    str(CHAR_UUID_WAVEMINI_DATA): WaveMiniDecode(
        name="WaveMini", format_type="<HHHHHHLL", scale=1.0
    ),
}

command_decoders = {
    str(COMMAND_UUID): CommandDecode(
        name="Battery", format_type="<L12B6H", cmd=struct.pack("<B", 0x6D)
    )
}


class AirthingsDevice:
    """Response data with information about the Airthings device"""

    hw_version: str
    sw_version: str
    name: str
    sensors: dict[str, str] = {}


class AirthingsBluetoothDeviceData:
    """Data for Airthings BLE sensors."""

    def __init__(
        self,
        logger: Logger,
        elevation: int,
        is_metric: bool,
        voltage: Tuple[float, float] = (2.4, 3.2),
    ):
        super().__init__()
        self.logger = logger
        self.is_metric = is_metric
        self.elevation = elevation
        self.voltage = voltage
        self._command_data = None
        self._event = None

    def notification_handler(self, _, data):
        """Helper for command events"""
        self._command_data = data
        self._event.set()

    async def _get_device_characteristics(
        self, client: BleakClient, device=AirthingsDevice
    ) -> AirthingsDevice:
        for characteristic in device_info_characteristics:
            data = await client.read_gatt_char(characteristic.uuid)
            if characteristic.name == "hardware_rev":
                device.hw_version = data.decode(characteristic.format)
                continue
            if characteristic.name == "firmware_rev":
                device.sw_version = data.decode(characteristic.format)
                continue
            if characteristic.name == "device_name":
                device.name = data.decode(characteristic.format)
        return device

    async def _get_service_characteristics(
        self, client: BleakClient, device=AirthingsDevice
    ) -> AirthingsDevice:
        svcs = await client.get_services()
        for service in svcs:
            for characteristic in service.characteristics:
                if (
                    characteristic.uuid in sensors_characteristics_uuid_str
                    and str(characteristic.uuid) in sensor_decoders
                ):
                    data = await client.read_gatt_char(characteristic.uuid)
                    sensor_data = sensor_decoders[
                        str(characteristic.uuid)
                    ].decode_data(data)

                    device.sensors.update(sensor_data)

                    # manage radon values
                    if d := sensor_data.get("radon_1day_avg"):
                        device.sensors["radon_1day_level"] = get_radon_level(d)
                        if not self.is_metric:
                            device.sensors["radon_1day_avg"] = (
                                d * BQ_TO_PCI_MULTIPLIER
                            )
                    if d := sensor_data.get("radon_longterm_avg"):
                        device.sensors[
                            "radon_longterm_level"
                        ] = get_radon_level(d)
                        if not self.is_metric:
                            device.sensors["radon_longterm_avg"] = (
                                d * BQ_TO_PCI_MULTIPLIER
                            )

                    # rel to abs pressure
                    if p := sensor_data["rel_atm_pressure"]:
                        device.sensors["pressure"] = get_absolute_pressure(
                            self.elevation, p
                        )

                        # remove rel atm
                        device.sensors.pop("rel_atm_pressure")

                if str(characteristic.uuid) in command_decoders:
                    self._event = asyncio.Event()
                    # Set up the notification handlers
                    await client.start_notify(
                        characteristic.uuid, self.notification_handler
                    )
                    # send command to this 'indicate' characteristic
                    await client.write_gatt_char(
                        characteristic.uuid,
                        command_decoders[str(characteristic.uuid)].cmd,
                    )
                    # Wait for up to one second to see if a
                    # callback comes in.
                    try:
                        await asyncio.wait_for(self._event.wait(), 1)
                    except asyncio.TimeoutError:
                        self.logger.warn("Timeout getting command data.")
                    if self._command_data is not None:
                        sensor_data = command_decoders[
                            str(characteristic.uuid)
                        ].decode_data(self._command_data)
                        self._command_data = None

                        # calculate battery percentage
                        v_min, v_max = self.voltage
                        bat = sensor_data["battery"]
                        bat_pct = (
                            max(
                                0,
                                min(
                                    100,
                                    round(
                                        (bat - v_min) / (v_max - v_min) * 100
                                    ),
                                ),
                            ),
                        )

                        device.sensors.update(
                            {
                                "illuminance": sensor_data["illuminance"],
                                "battery": bat_pct,
                            }
                        )
                    # Stop notification handler
                    await client.stop_notify(characteristic.uuid)

        return device

    async def update_device(self, ble_device: BLEDevice) -> AirthingsDevice:
        """Connects to the device through BLE and retrieves relevant data"""
        client = await establish_connection(
            BleakClient, ble_device, ble_device.address
        )

        device = AirthingsDevice
        device = await self._get_device_characteristics(client, device)
        device = await self._get_service_characteristics(client, device)
        await client.disconnect()

        return device
