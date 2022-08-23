"""Parser for Airthings BLE devices"""

from __future__ import annotations

import asyncio
import struct
from collections import namedtuple
from datetime import datetime
from logging import Logger
from math import exp
from typing import Any, Callable, Tuple

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
    name: str, format_type: str, scale: float
) -> Callable[[bytearray], dict[str, float | None | str]]:
    """same as base decoder, but expects only one value.. for real"""

    def handler(raw_data: bytearray) -> dict[str, float | None | str]:
        val = struct.unpack(format_type, raw_data)
        res: float | None = None
        if len(val) == 1:
            res = val[0] * scale
        data: dict[str, float | None | str] = {name: res}
        return data

    return handler


def __decode_wave_plus(
    name: str, format_type: str, scale: float
) -> Callable[[bytearray], dict[str, float | None | str]]:
    def handler(raw_data: bytearray) -> dict[str, float | None | str]:
        vals = _decode_base(name, format_type, scale)(raw_data)
        val = vals[name]
        data: dict[str, float | None | str] = {}
        data["date_time"] = str(datetime.isoformat(datetime.now()))
        data["humidity"] = val[1] / 2.0
        data["radon_1day_avg"] = val[4] if 0 <= val[4] <= 16383 else None
        data["radon_longterm_avg"] = val[5] if 0 <= val[5] <= 16383 else None
        data["temperature"] = val[6] / 100.0
        data["rel_atm_pressure"] = val[7] / 50.0
        data["co2"] = val[8] * 1.0
        data["voc"] = val[9] * 1.0
        return data

    return handler


def __decode_wave_2(
    name: str, format_type: str, scale: float
) -> Callable[[bytearray], dict[str, float | None | str]]:
    def handler(raw_data: bytearray) -> dict[str, float | None | str]:
        vals = _decode_base(name, format_type, scale)(raw_data)
        val = vals[name]
        data: dict[str, float | None | str] = {}
        data["date_time"] = str(datetime.isoformat(datetime.now()))
        data["humidity"] = val[1] / 2.0
        data["radon_1day_avg"] = val[4] if 0 <= val[4] <= 16383 else None
        data["radon_longterm_avg"] = val[5] if 0 <= val[5] <= 16383 else None
        data["temperature"] = val[6] / 100.0
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
        data["temperature"] = round(val[1] / 100.0 - 273.15, 2)
        data["humidity"] = val[3] / 100.0
        data["voc"] = val[4] * 1.0
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
        data["illuminance"] = str(val[0] * scale)
        data["accelerometer"] = str(val[1] * scale)
        return data

    return handler


# pylint: disable=too-few-public-methods
class CommandDecode:
    """Decoder for the command response"""

    cmd: bytes | bytearray

    def __init__(self, name: str, format_type: str, cmd: bytes):
        """Initialize command decoder"""
        self.name = name
        self.format_type = format_type
        self.cmd = cmd

    def decode_data(
        self, raw_data: bytearray | None
    ) -> dict[str, float | str | None]:
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


def get_radon_level(data: float) -> str:
    """Returns the applicable radon level"""
    if data <= VERY_LOW[1]:
        radon_level = VERY_LOW[2]
    elif data <= LOW[1]:
        radon_level = LOW[2]
    elif data <= MODERATE[1]:
        radon_level = MODERATE[2]
    else:
        radon_level = HIGH[2]
    return radon_level


# pylint: disable=invalid-name
def get_absolute_pressure(elevation: int, data: float) -> float:
    """Returns an absolute pressure calculated from the given elevation"""
    p0 = 101325  # Pa
    g = 9.80665  # m/s^2
    M = 0.02896968  # kg/mol
    T0 = 288.16  # K
    R0 = 8.314462618  # J/(mol K)
    h = elevation  # m
    offset = (p0 - (p0 * exp(-g * h * M / (T0 * R0)))) / 100.0  # mbar
    return data + round(offset, 2)


sensor_decoders: dict[
    str,
    Callable[[bytearray], dict[str, float | None | str]],
] = {
    str(CHAR_UUID_WAVE_PLUS_DATA): __decode_wave_plus(
        name="Pluss", format_type="BBBBHHHHHHHH", scale=0
    ),
    str(CHAR_UUID_DATETIME): _decode_wave(
        name="date_time", format_type="HBBBBB", scale=0
    ),
    str(CHAR_UUID_HUMIDITY): _decode_attr(
        name="humidity", format_type="H", scale=1.0 / 100.0
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
    str(CHAR_UUID_WAVE_2_DATA): __decode_wave_2(
        name="Wave2", format_type="<4B8H", scale=1.0
    ),
    str(CHAR_UUID_WAVEMINI_DATA): _decode_wave_mini(
        name="WaveMini", format_type="<HHHHHHLL", scale=1.0
    ),
}

command_decoders: dict[str, CommandDecode] = {
    str(COMMAND_UUID): CommandDecode(
        name="Battery", format_type="<L12B6H", cmd=struct.pack("<B", 0x6D)
    )
}


def short_address(address: str) -> str:
    """Convert a Bluetooth address to a short address."""
    return address.replace("-", "").replace(":", "")[-6:].upper()


class AirthingsDevice:
    """Response data with information about the Airthings device"""

    hw_version: str
    sw_version: str
    name: str
    identifier: str
    sensors: dict[str, str | float | None] = {}
    address: str


class AirthingsBluetoothDeviceData:
    """Data for Airthings BLE sensors."""

    _event: asyncio.Event | None
    _command_data: bytearray | None

    def __init__(
        self,
        logger: Logger,
        elevation: int | None = None,
        is_metric: bool = True,
        voltage: tuple[float, float] = (2.4, 3.2),
    ):
        super().__init__()
        self.logger = logger
        self.is_metric = is_metric
        self.elevation = elevation
        self.voltage = voltage
        self._command_data = None
        self._event = None

    def notification_handler(self, _: Any, data: bytearray) -> None:
        """Helper for command events"""
        self._command_data = data
        if self._event is None:
            return
        self._event.set()

    async def _get_device_characteristics(
        self, client: BleakClient, device: AirthingsDevice
    ) -> AirthingsDevice:
        device.identifier = short_address(client.address)
        device.address = client.address

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
        self, client: BleakClient, device: AirthingsDevice
    ) -> AirthingsDevice:
        svcs = await client.get_services()
        for service in svcs:
            for characteristic in service.characteristics:
                if (
                    characteristic.uuid in sensors_characteristics_uuid_str
                    and str(characteristic.uuid) in sensor_decoders
                ):
                    data = await client.read_gatt_char(characteristic.uuid)

                    sensor_data = sensor_decoders[str(characteristic.uuid)](
                        data
                    )
                    # skip for now!

                    sensor_data.pop("date_time")

                    device.sensors.update(sensor_data)

                    # manage radon values
                    if d := sensor_data.get("radon_1day_avg"):
                        device.sensors["radon_1day_level"] = get_radon_level(
                            float(d)
                        )
                        if not self.is_metric:
                            device.sensors["radon_1day_avg"] = (
                                float(d) * BQ_TO_PCI_MULTIPLIER
                            )
                    if d := sensor_data.get("radon_longterm_avg"):
                        device.sensors[
                            "radon_longterm_level"
                        ] = get_radon_level(float(d))
                        if not self.is_metric:
                            device.sensors["radon_longterm_avg"] = (
                                float(d) * BQ_TO_PCI_MULTIPLIER
                            )

                    # rel to abs pressure
                    if p := sensor_data["rel_atm_pressure"] and self.elevation:
                        device.sensors["pressure"] = (
                            get_absolute_pressure(self.elevation, float(p))
                            if self.elevation is not None
                            else p
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
                        bytearray(
                            command_decoders[str(characteristic.uuid)].cmd
                        ),
                    )
                    # Wait for up to one second to see if a
                    # callback comes in.
                    try:
                        await asyncio.wait_for(self._event.wait(), 1)
                    except asyncio.TimeoutError:
                        self.logger.warn("Timeout getting command data.")

                    if self._command_data is not None:
                        command_sensor_data = command_decoders[
                            str(characteristic.uuid)
                        ].decode_data(self._command_data)
                        self._command_data = None

                        # calculate battery percentage
                        v_min, v_max = self.voltage
                        bat_pct: int | None
                        if command_sensor_data["battery"] is not None:
                            bat = float(command_sensor_data["battery"])
                            # set as tuple during lint somehow..
                            bat_pct = (
                                max(
                                    0,
                                    min(
                                        100,
                                        round(
                                            (bat - v_min)
                                            / (v_max - v_min)
                                            * 100
                                        ),
                                    ),
                                ),
                            )[0]

                        device.sensors.update(
                            {
                                "illuminance": command_sensor_data[
                                    "illuminance"
                                ],
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

        device = AirthingsDevice()

        device = await self._get_device_characteristics(client, device)
        device = await self._get_service_characteristics(client, device)
        await client.disconnect()

        return device
