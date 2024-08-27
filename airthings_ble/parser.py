"""Parser for Airthings BLE devices"""

from __future__ import annotations

import asyncio
import dataclasses
import re
import struct
import sys
from collections import namedtuple
from datetime import datetime
from functools import partial
from logging import Logger
from typing import Any, Callable, Optional, Tuple

from async_interrupt import interrupt
from bleak import BleakClient, BleakError
from bleak.backends.device import BLEDevice
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from .const import (
    DEFAULT_MAX_UPDATE_ATTEMPTS,
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
    CO2_MAX,
    COMMAND_UUID_WAVE_2,
    COMMAND_UUID_WAVE_MINI,
    COMMAND_UUID_WAVE_PLUS,
    HIGH,
    LOW,
    MODERATE,
    PERCENTAGE_MAX,
    RADON_MAX,
    TEMPERATURE_MAX,
    UPDATE_TIMEOUT,
    VERY_LOW,
    VOC_MAX,
)
from .device_type import AirthingsDeviceType

if sys.version_info[:2] < (3, 11):
    from async_timeout import timeout as asyncio_timeout
else:
    from asyncio import timeout as asyncio_timeout

Characteristic = namedtuple("Characteristic", ["uuid", "name", "format"])

wave_gen_1_device_info_characteristics = [
    Characteristic(CHAR_UUID_MANUFACTURER_NAME, "manufacturer", "utf-8"),
    Characteristic(CHAR_UUID_SERIAL_NUMBER_STRING, "serial_nr", "utf-8"),
    Characteristic(CHAR_UUID_DEVICE_NAME, "device_name", "utf-8"),
    Characteristic(CHAR_UUID_FIRMWARE_REV, "firmware_rev", "utf-8"),
]
device_info_characteristics = wave_gen_1_device_info_characteristics + [
    Characteristic(CHAR_UUID_HARDWARE_REV, "hardware_rev", "utf-8"),
]
_CHARS_BY_MODELS = {
    "2900": wave_gen_1_device_info_characteristics,
}

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
    COMMAND_UUID_WAVE_2,
    COMMAND_UUID_WAVE_PLUS,
    COMMAND_UUID_WAVE_MINI,
]
sensors_characteristics_uuid_str = [str(x) for x in sensors_characteristics_uuid]


class DisconnectedError(Exception):
    """Disconnected from device."""


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
        data["pressure"] = float(val[7] / 50.0)
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


class CommandDecode:
    """Decoder for the command response"""

    cmd: bytes = b"\x6D"
    format_type: str

    def decode_data(
        self,
        logger: Logger,
        raw_data: bytearray | None,  # pylint: disable=unused-argument
    ) -> dict[str, float | str | None] | None:
        """Decoder returns dict with battery"""
        logger.debug("Command decoder not implemented")
        return {}

    def validate_data(
        self, logger: Logger, raw_data: bytearray | None
    ) -> Optional[Any]:
        """Validate data. Make sure the data is for the command."""
        if raw_data is None:
            logger.debug("Validate data: No data received")
            return None

        cmd = raw_data[0:1]
        if cmd != self.cmd:
            logger.warning(
                "Result for wrong command received, expected %s got %s",
                self.cmd.hex(),
                cmd.hex(),
            )
            return None

        if len(raw_data[2:]) != struct.calcsize(self.format_type):
            logger.warning(
                "Wrong length data received (%s) versus expected (%s)",
                len(raw_data[2:]),
                struct.calcsize(self.format_type),
            )
            return None

        return struct.unpack(self.format_type, raw_data[2:])

    def make_data_receiver(self) -> _NotificationReceiver:
        """Creates a notification receiver for the command."""
        return _NotificationReceiver(struct.calcsize(self.format_type))


class WaveRadonAndPlusCommandDecode(CommandDecode):
    """Decoder for the Wave Plus command response"""

    def __init__(self) -> None:
        """Initialize command decoder"""
        self.format_type = "<L2BH2B9H"

    def decode_data(
        self, logger: Logger, raw_data: bytearray | None
    ) -> dict[str, float | str | None] | None:
        """Decoder returns dict with battery"""

        if val := self.validate_data(logger, raw_data):
            res = {}
            res["battery"] = val[13] / 1000.0
            return res

        return None


class WaveMiniCommandDecode(CommandDecode):
    """Decoder for the Wave Radon command response"""

    def __init__(self) -> None:
        """Initialize command decoder"""
        self.format_type = "<2L4B2HL4HL"

    def decode_data(
        self, logger: Logger, raw_data: bytearray | None
    ) -> dict[str, float | str | None] | None:
        """Decoder returns dict with battery"""

        if val := self.validate_data(logger, raw_data):
            res = {}
            res["battery"] = val[11] / 1000.0

            return res

        return None


class _NotificationReceiver:
    """Receiver for a single notification message.

    A notification message that is larger than the MTU can get sent over multiple
    packets. This receiver knows how to reconstruct it.
    """

    message: bytearray | None

    def __init__(self, message_size: int):
        self.message = None
        self._message_size = message_size
        self._loop = asyncio.get_running_loop()
        self._future: asyncio.Future[None] = self._loop.create_future()

    def _full_message_received(self) -> bool:
        return self.message is not None and len(self.message) >= self._message_size

    def __call__(self, _: Any, data: bytearray) -> None:
        if self.message is None:
            self.message = data
        elif not self._full_message_received():
            self.message += data
        if self._full_message_received():
            self._future.set_result(None)

    def _on_timeout(self) -> None:
        if not self._future.done():
            self._future.set_exception(
                asyncio.TimeoutError("Timeout waiting for message")
            )

    async def wait_for_message(self, timeout: float) -> None:
        """Waits until the full message is received.

        If the full message has already been received, this method returns immediately.
        """
        if not self._full_message_received():
            timer_handle = self._loop.call_later(timeout, self._on_timeout)
            try:
                await self._future
            finally:
                timer_handle.cancel()


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


sensor_decoders: dict[
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

command_decoders: dict[str, CommandDecode] = {
    str(COMMAND_UUID_WAVE_2): WaveRadonAndPlusCommandDecode(),
    str(COMMAND_UUID_WAVE_PLUS): WaveRadonAndPlusCommandDecode(),
    str(COMMAND_UUID_WAVE_MINI): WaveMiniCommandDecode(),
}


def short_address(address: str) -> str:
    """Convert a Bluetooth address to a short address."""
    return address.replace("-", "").replace(":", "")[-6:].upper()


# pylint: disable=too-many-instance-attributes


@dataclasses.dataclass
class AirthingsDeviceInfo:
    """Response data with information about the Airthings device without sensors."""

    manufacturer: str = ""
    hw_version: str = ""
    sw_version: str = ""
    model: AirthingsDeviceType = AirthingsDeviceType.UNKNOWN
    name: str = ""
    identifier: str = ""
    address: str = ""
    did_first_sync: bool = False

    def friendly_name(self) -> str:
        """Generate a name for the device."""

        return f"Airthings {self.model.product_name}"


@dataclasses.dataclass
class AirthingsDevice(AirthingsDeviceInfo):
    """Response data with information about the Airthings device"""

    sensors: dict[str, str | float | None] = dataclasses.field(
        default_factory=lambda: {}
    )

    def friendly_name(self) -> str:
        """Generate a name for the device."""

        return f"Airthings {self.model.product_name}"


# pylint: disable=too-many-locals
# pylint: disable=too-many-branches
# pylint: disable=too-few-public-methods
class AirthingsBluetoothDeviceData:
    """Data for Airthings BLE sensors."""

    def __init__(
        self,
        logger: Logger,
        is_metric: bool = True,
        max_attempts: int = DEFAULT_MAX_UPDATE_ATTEMPTS,
    ) -> None:
        """Initialize the Airthings BLE sensor data object."""
        self.logger = logger
        self.is_metric = is_metric
        self.device_info = AirthingsDeviceInfo()
        self.max_attempts = max_attempts

    def set_max_attempts(self, max_attempts: int) -> None:
        """Set the number of attempts."""
        self.max_attempts = max_attempts

    async def _get_device_characteristics(
        self, client: BleakClient, device: AirthingsDevice
    ) -> None:
        device_info = self.device_info
        device_info.address = client.address
        did_first_sync = device_info.did_first_sync

        # We need to fetch model to determ what to fetch.
        if not did_first_sync:
            try:
                data = await client.read_gatt_char(CHAR_UUID_MODEL_NUMBER_STRING)
            except BleakError as err:
                self.logger.debug("Get device characteristics exception: %s", err)
                return

            device_info.model = AirthingsDeviceType.from_raw_value(data.decode("utf-8"))
            if device_info.model == AirthingsDeviceType.UNKNOWN:
                self.logger.warning(
                    "Could not map model number to model name, "
                    "most likely an unsupported device: %s",
                    data.decode("utf-8"),
                )

        characteristics = _CHARS_BY_MODELS.get(
            device_info.model.raw_value, device_info_characteristics
        )
        for characteristic in characteristics:
            if did_first_sync and characteristic.name != "firmware_rev":
                # Only the sw_version can change once set, so we can skip the rest.
                continue

            try:
                data = await client.read_gatt_char(characteristic.uuid)
            except BleakError as err:
                self.logger.debug("Get device characteristics exception: %s", err)
                continue
            if characteristic.name == "manufacturer":
                device_info.manufacturer = data.decode(characteristic.format)
            elif characteristic.name == "hardware_rev":
                device_info.hw_version = data.decode(characteristic.format)
            elif characteristic.name == "firmware_rev":
                device_info.sw_version = data.decode(characteristic.format)
            elif characteristic.name == "device_name":
                device_info.name = data.decode(characteristic.format)
            elif characteristic.name == "serial_nr":
                identifier = data.decode(characteristic.format)
                # Some devices return `Serial Number` on Mac instead of
                # the actual serial number.
                if identifier != "Serial Number":
                    device_info.identifier = identifier
            else:
                self.logger.debug(
                    "Characteristics not handled: %s", characteristic.uuid
                )

        if (
            device_info.model == AirthingsDeviceType.WAVE_GEN_1
            and device_info.name
            and not device_info.identifier
        ):
            # For the Wave gen. 1 we need to fetch the identifier in the device name.
            # Example: From `AT#123456-2900Radon` we need to fetch `123456`.
            wave1_identifier = re.search(r"(?<=\#)[0-9]{1,6}", device_info.name)
            if wave1_identifier is not None and len(wave1_identifier.group()) == 6:
                device_info.identifier = wave1_identifier.group()

        # In some cases the device name will be empty, for example when using a Mac.
        if not device_info.name:
            device_info.name = device_info.friendly_name()

        if device_info.model:
            device_info.did_first_sync = True

        # Copy the cached device_info to device
        for field in dataclasses.fields(device_info):
            name = field.name
            setattr(device, name, getattr(device_info, name))

    async def _get_service_characteristics(
        self, client: BleakClient, device: AirthingsDevice
    ) -> None:
        svcs = client.services
        sensors = device.sensors
        for service in svcs:
            for characteristic in service.characteristics:
                uuid = characteristic.uuid
                uuid_str = str(uuid)
                if (
                    uuid in sensors_characteristics_uuid_str
                    and uuid_str in sensor_decoders
                ):
                    try:
                        data = await client.read_gatt_char(characteristic)
                    except BleakError as err:
                        self.logger.debug(
                            "Get service characteristics exception: %s", err
                        )
                        continue

                    sensor_data = sensor_decoders[uuid_str](data)

                    # Skipping for now
                    if "date_time" in sensor_data:
                        sensor_data.pop("date_time")

                    sensors.update(sensor_data)

                    # Manage radon values
                    if (d := sensor_data.get("radon_1day_avg")) is not None:
                        sensors["radon_1day_level"] = get_radon_level(float(d))
                        if not self.is_metric:
                            sensors["radon_1day_avg"] = float(d) * BQ_TO_PCI_MULTIPLIER
                    if (d := sensor_data.get("radon_longterm_avg")) is not None:
                        sensors["radon_longterm_level"] = get_radon_level(float(d))
                        if not self.is_metric:
                            sensors["radon_longterm_avg"] = (
                                float(d) * BQ_TO_PCI_MULTIPLIER
                            )

                if uuid_str in command_decoders:
                    decoder = command_decoders[uuid_str]
                    command_data_receiver = decoder.make_data_receiver()

                    # Set up the notification handlers
                    await client.start_notify(characteristic, command_data_receiver)
                    # send command to this 'indicate' characteristic
                    await client.write_gatt_char(characteristic, bytearray(decoder.cmd))
                    # Wait for up to one second to see if a callback comes in.
                    try:
                        await command_data_receiver.wait_for_message(5)
                    except asyncio.TimeoutError:
                        self.logger.warning("Timeout getting command data.")

                    command_sensor_data = decoder.decode_data(
                        self.logger, command_data_receiver.message
                    )
                    if command_sensor_data is not None:
                        new_values: dict[str, float | str | None] = {}

                        if (bat_data := command_sensor_data.get("battery")) is not None:
                            new_values["battery"] = device.model.battery_percentage(
                                float(bat_data)
                            )

                        if illuminance := command_sensor_data.get("illuminance"):
                            new_values["illuminance"] = illuminance

                        sensors.update(new_values)

                    # Stop notification handler
                    await client.stop_notify(characteristic)

    def _handle_disconnect(
        self, disconnect_future: asyncio.Future[bool], client: BleakClient
    ) -> None:
        """Handle disconnect from device."""
        self.logger.debug("Disconnected from %s", client.address)
        if not disconnect_future.done():
            disconnect_future.set_result(True)

    async def update_device(self, ble_device: BLEDevice) -> AirthingsDevice:
        """Connects to the device through BLE and retrieves relevant data"""
        for attempt in range(self.max_attempts):
            is_final_attempt = attempt == self.max_attempts - 1
            try:
                return await self._update_device(ble_device)
            except DisconnectedError:
                if is_final_attempt:
                    raise
                self.logger.debug(
                    "Unexpectedly disconnected from %s", ble_device.address
                )
            except BleakError as err:
                if is_final_attempt:
                    raise
                self.logger.debug("Bleak error: %s", err)
        raise RuntimeError("Should not reach this point")

    async def _update_device(self, ble_device: BLEDevice) -> AirthingsDevice:
        """Connects to the device through BLE and retrieves relevant data"""
        device = AirthingsDevice()
        loop = asyncio.get_running_loop()
        disconnect_future = loop.create_future()
        client: BleakClientWithServiceCache = (
            await establish_connection(  # pylint: disable=line-too-long
                BleakClientWithServiceCache,  # type: ignore
                ble_device,
                ble_device.address,
                disconnected_callback=partial(
                    self._handle_disconnect, disconnect_future
                ),
            )
        )
        try:
            async with interrupt(
                disconnect_future,
                DisconnectedError,
                f"Disconnected from {client.address}",
            ), asyncio_timeout(UPDATE_TIMEOUT):
                await self._get_device_characteristics(client, device)
                await self._get_service_characteristics(client, device)
        except BleakError as err:
            if "not found" in str(err):  # In future bleak this is a named exception
                # Clear the char cache since a char is likely
                # missing from the cache
                await client.clear_cache()
            raise
        finally:
            await client.disconnect()

        return device
