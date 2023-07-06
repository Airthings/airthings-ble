"""Parser for Airthings BLE devices"""

from __future__ import annotations

import asyncio
import dataclasses
import re
import struct
from collections import namedtuple
from datetime import datetime
from logging import Logger
from math import exp
from typing import Any, Callable, Tuple

from bleak import BleakClient, BleakError
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection

from .const import (
    ALL_CHARACTERISTICS,
    BQ_TO_PCI_MULTIPLIER,
    CHAR_UUID_DATETIME,
    CHAR_UUID_DEVICE_NAME,
    CHAR_UUID_FIRMWARE_REV,
    CHAR_UUID_HARDWARE_REV,
    CHAR_UUID_HUMIDITY,
    CHAR_UUID_ILLUMINANCE_ACCELEROMETER,
    CHAR_UUID_MODEL_NUMBER_STRING,
    CHAR_UUID_RADON_1DAYAVG,
    CHAR_UUID_RADON_LONG_TERM_AVG,
    CHAR_UUID_SERIAL_NUMBER_STRING,
    CHAR_UUID_TEMPERATURE,
    CHAR_UUID_WAVE_2_DATA,
    CHAR_UUID_WAVE_PLUS_DATA,
    CHAR_UUID_WAVEMINI_DATA,
    COMMAND_UUID,
    DEVICE_TYPE,
    HIGH,
    LOW,
    MODERATE,
    VERY_LOW,
)

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
sensors_characteristics_uuid_str = [str(x) for x in sensors_characteristics_uuid]


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
        self, logger: Logger, raw_data: bytearray | None
    ) -> dict[str, float | str | None] | None:
        """Decoder returns dict with illuminance and battery"""
        if raw_data is None:
            return None

        cmd = raw_data[0:1]
        if cmd != self.cmd:
            logger.debug(
                "Result for wrong command received, expected %s got %s",
                self.cmd.hex(),
                cmd.hex(),
            )
            return None

        if len(raw_data[2:]) != struct.calcsize(self.format_type):
            logger.debug(
                "Wrong length data received (%s) versus expected (%s)",
                len(cmd),
                struct.calcsize(self.format_type),
            )
            return None
        val = struct.unpack(self.format_type, raw_data[2:])
        res = {}
        res["illuminance"] = val[2]
        # res['measurement_periods'] =  val[5]
        res["battery"] = val[17] / 1000.0

        return res

    def make_data_receiver(self) -> _NotificationReceiver:
        """Creates a notification receiver for the command."""
        return _NotificationReceiver(struct.calcsize(self.format_type))


class _NotificationReceiver:
    """Receiver for a single notification message.

    A notification message that is larger than the MTU can get sent over multiple packets. This
    receiver knows how to reconstruct it.
    """

    message: bytearray | None

    def __init__(self, message_size: int):
        self.message = None
        self._message_size = message_size
        self._event = asyncio.Event()

    def _full_message_received(self) -> bool:
        return self.message is not None and len(self.message) >= self._message_size

    def __call__(self, _: Any, data: bytearray) -> None:
        if self.message is None:
            self.message = data
        elif not self._full_message_received():
            self.message += data
        if self._full_message_received():
            self._event.set()

    async def wait_for_message(self) -> None:
        """Waits until the full message is received.

        If the full message has already been received, this method returns immediately."""
        if not self._full_message_received():
            await self._event.wait()


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


sensor_decoders: dict[str, Callable[[bytearray], dict[str, float | None | str]],] = {
    str(CHAR_UUID_WAVE_PLUS_DATA): __decode_wave_plus(
        name="Plus", format_type="BBBBHHHHHHHH", scale=0
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


@dataclasses.dataclass
class AirthingsDevice:
    """Response data with information about the Airthings device"""

    hw_version: str = ""
    sw_version: str = ""
    model: str = ""
    model_raw: str = ""
    name: str = ""
    identifier: str = ""
    address: str = ""
    sensors: dict[str, str | float | None] = dataclasses.field(
        default_factory=lambda: {}
    )


# pylint: disable=too-many-locals
# pylint: disable=too-many-branches
class AirthingsBluetoothDeviceData:
    """Data for Airthings BLE sensors."""

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

    async def _get_device_characteristics(
        self, client: BleakClient, device: AirthingsDevice
    ) -> AirthingsDevice:
        device.address = client.address

        # First we need to fetch model. With this we can determ what to fetch.
        try:
            data = await client.read_gatt_char(CHAR_UUID_MODEL_NUMBER_STRING)
        except BleakError as err:
            self.logger.debug("Get device characteristics exception: %s", err)
            return device
        device.model_raw = str(data.decode("utf-8"))

        config = DEVICE_TYPE.get(device.model_raw)
        if config is not None:
            characteristics = config["characteristics"]
            device.model = config.get("name")
        else:
            self.logger.debug(
                "Could not map model number to model name, most likely an unsupported device: %s",
                device.model_raw,
            )
            characteristics = ALL_CHARACTERISTICS

        for characteristic in characteristics:
            try:
                data = await client.read_gatt_char(characteristic)
            except BleakError as err:
                self.logger.debug("Get device characteristics exception: %s", err)
                continue
            if characteristic == CHAR_UUID_HARDWARE_REV:
                device.hw_version = data.decode("utf-8")
                self.logger.debug(
                    "Saved hw version: %s, model: %s",
                    device.hw_version,
                    device.model_raw,
                )
            elif characteristic == CHAR_UUID_FIRMWARE_REV:
                device.sw_version = data.decode("utf-8")
                self.logger.debug(
                    "Saved sw version: %s, model: %s",
                    device.sw_version,
                    device.model_raw,
                )
            elif characteristic == CHAR_UUID_DEVICE_NAME:
                device.name = data.decode("utf-8")
                self.logger.debug(
                    "Saved name: %s, model: %s", device.name, device.model_raw
                )
            elif characteristic == CHAR_UUID_SERIAL_NUMBER_STRING:
                identifier = data.decode("utf-8")
                # Some devices return `Serial Number` on Mac instead of the actual serial number.
                if identifier != "Serial Number":
                    device.identifier = identifier
                    self.logger.debug(
                        "Saved identifier: %s, model: %s",
                        device.identifier,
                        device.model_raw,
                    )
                else:
                    self.logger.debug(
                        "Identifier not saved...: %s, model: %s",
                        identifier,
                        device.model_raw,
                    )
            else:
                self.logger.debug(
                    "Characteristics not handled: %s", characteristic.uuid
                )

        if (
            device.model_raw == "2900"
            and device.name != ""
            and (device.identifier == "" or device.identifier is None)
        ):
            self.logger.warning("Current identifier for 2900: %s", device.identifier)
            self.logger.warning("Current name for 2900: %s", device.name)
            # For the Wave gen. 1 we need to fetch the identifier in the device name.
            # Example: From `AT#123456-2900Radon` we need to fetch `123456`.
            identifier = re.search("(?<=\#)[0-9]{1,6}", device.name)
            self.logger.warning("Generated identifier for 2900: %s", identifier.string)
            if identifier.group() is not None and len(identifier.group()) == 6:
                device.identifier = identifier

        if device.name == "":
            name = f"Airthings {device.model}"
            device.name = name
            self.logger.debug("Generating name 1: %s", device.name)
        if device.identifier != "":
            device.name += f" ({device.identifier})"
            self.logger.debug("Generating name 2: %s", device.name)

        if device.model_raw == "":
            self.logger.warning("Missing `model_raw`, model: %s", device.model)
        if device.model == "":
            self.logger.warning("Missing `model`, model: %s", device.model)
        if device.hw_version == "":
            self.logger.warning("Missing `hw_version`, model: %s", device.model)
        if device.sw_version == "":
            self.logger.warning("Missing `sw_version`, model: %s", device.model)
        if device.name == "":
            self.logger.warning("Missing `name`, model: %s", device.model)
        if device.identifier == "":
            self.logger.warning("Missing `identifier`, model: %s", device.model)
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
                    try:
                        data = await client.read_gatt_char(characteristic.uuid)
                    except BleakError as err:
                        self.logger.debug(
                            "Get service characteristics exception: %s", err
                        )
                        continue
                    data = await client.read_gatt_char(characteristic.uuid)

                    sensor_data = sensor_decoders[str(characteristic.uuid)](data)
                    # skip for now!

                    if "date_time" in sensor_data:
                        sensor_data.pop("date_time")

                    device.sensors.update(sensor_data)

                    # manage radon values
                    if d := sensor_data.get("radon_1day_avg"):
                        device.sensors["radon_1day_level"] = get_radon_level(float(d))
                        if not self.is_metric:
                            device.sensors["radon_1day_avg"] = (
                                float(d) * BQ_TO_PCI_MULTIPLIER
                            )
                    if d := sensor_data.get("radon_longterm_avg"):
                        device.sensors["radon_longterm_level"] = get_radon_level(
                            float(d)
                        )
                        if not self.is_metric:
                            device.sensors["radon_longterm_avg"] = (
                                float(d) * BQ_TO_PCI_MULTIPLIER
                            )

                    # rel to abs pressure
                    if pressure := sensor_data.get("rel_atm_pressure"):
                        device.sensors["pressure"] = (
                            get_absolute_pressure(self.elevation, float(pressure))
                            if self.elevation is not None
                            else pressure
                        )

                    # remove rel atm
                    device.sensors.pop("rel_atm_pressure", None)

                if str(characteristic.uuid) in command_decoders:
                    decoder = command_decoders[str(characteristic.uuid)]
                    command_data_receiver = decoder.make_data_receiver()
                    # Set up the notification handlers
                    await client.start_notify(
                        characteristic.uuid, command_data_receiver
                    )
                    # send command to this 'indicate' characteristic
                    await client.write_gatt_char(
                        characteristic.uuid, bytearray(decoder.cmd)
                    )
                    # Wait for up to one second to see if a callback comes in.
                    try:
                        await asyncio.wait_for(
                            command_data_receiver.wait_for_message(), 1
                        )
                    except asyncio.TimeoutError:
                        self.logger.warning("Timeout getting command data.")

                    command_sensor_data = decoder.decode_data(
                        self.logger, command_data_receiver.message
                    )
                    if command_sensor_data is not None:
                        # calculate battery percentage
                        v_min, v_max = self.voltage
                        bat_pct: int | None = None
                        bat_data = command_sensor_data.get("battery")
                        if bat_data is not None:
                            bat = float(bat_data)
                            # set as tuple during lint somehow..
                            bat_pct = (
                                max(
                                    0,
                                    min(
                                        100,
                                        round((bat - v_min) / (v_max - v_min) * 100),
                                    ),
                                ),
                            )[0]

                        device.sensors.update(
                            {
                                "illuminance": command_sensor_data.get("illuminance"),
                                "battery": bat_pct,
                            }
                        )

                    # Stop notification handler
                    await client.stop_notify(characteristic.uuid)

        return device

    async def update_device(self, ble_device: BLEDevice) -> AirthingsDevice:
        """Connects to the device through BLE and retrieves relevant data"""
        device = AirthingsDevice()
        client = await establish_connection(BleakClient, ble_device, ble_device.address)
        try:
            device = await self._get_device_characteristics(client, device)
            device = await self._get_service_characteristics(client, device)
        finally:
            await client.disconnect()

        return device
