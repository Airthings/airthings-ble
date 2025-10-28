"""Parser for Airthings BLE devices"""

from __future__ import annotations

import asyncio
import dataclasses
import re
from collections import namedtuple
from functools import partial
from logging import Logger

from async_interrupt import interrupt
from bleak import BleakClient, BleakError
from bleak.backends.device import BLEDevice
from bleak.backends.service import BleakGATTService
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from airthings_ble.airthings_firmware import AirthingsFirmwareVersion
from airthings_ble.atom.request_path import AtomRequestPath
from airthings_ble.command_decode import COMMAND_DECODERS, AtomCommandDecode
from airthings_ble.radon_level import get_radon_level
from airthings_ble.sensor_decoders import SENSOR_DECODERS

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
    COMMAND_UUID_ATOM,
    COMMAND_UUID_ATOM_NOTIFY,
    COMMAND_UUID_WAVE_2,
    COMMAND_UUID_WAVE_MINI,
    COMMAND_UUID_WAVE_PLUS,
    DEFAULT_MAX_UPDATE_ATTEMPTS,
    UPDATE_TIMEOUT,
)
from .device_type import AirthingsDeviceType

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


class UnsupportedDeviceError(Exception):
    """Unsupported device."""


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

    firmware = AirthingsFirmwareVersion()

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

        device.firmware.update_current_version(device_info.sw_version)

        # We need to fetch model to determ what to fetch.
        if not did_first_sync:
            try:
                data = await client.read_gatt_char(CHAR_UUID_MODEL_NUMBER_STRING)
            except BleakError as err:
                self.logger.debug("Get device characteristics exception: %s", err)
                return

            device_info.model = AirthingsDeviceType.from_raw_value(data.decode("utf-8"))
            if device_info.model == AirthingsDeviceType.UNKNOWN:
                raise UnsupportedDeviceError(
                    f"Model {data.decode('utf-8')} is not supported"
                )

        characteristics = _CHARS_BY_MODELS.get(
            device_info.model.raw_value, device_info_characteristics
        )

        self.logger.debug("Fetching device info characteristics: %s", characteristics)

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
            if (
                (
                    str(COMMAND_UUID_ATOM)
                    in (str(x.uuid) for x in service.characteristics)
                )
                and (
                    str(COMMAND_UUID_ATOM_NOTIFY)
                    in (str(x.uuid) for x in service.characteristics)
                )
                and device.model in AirthingsDeviceType.atom_devices()
            ):
                await self._atom_sensor_data(client, device, sensors, service)
            else:
                await self._wave_sensor_data(client, device, sensors, service)

    async def _wave_sensor_data(
        self,
        client: BleakClient,
        device: AirthingsDevice,
        sensors: dict[str, str | float | None],
        service: BleakGATTService,
    ) -> None:
        for characteristic in service.characteristics:
            uuid = characteristic.uuid
            uuid_str = str(uuid)
            if uuid in sensors_characteristics_uuid_str and uuid_str in SENSOR_DECODERS:
                try:
                    data = await client.read_gatt_char(characteristic)
                except BleakError as err:
                    self.logger.debug("Get service characteristics exception: %s", err)
                    continue

                sensor_data = SENSOR_DECODERS[uuid_str](data)

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
                        sensors["radon_longterm_avg"] = float(d) * BQ_TO_PCI_MULTIPLIER

            if uuid_str in COMMAND_DECODERS:
                decoder = COMMAND_DECODERS[uuid_str]
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
                    logger=self.logger, raw_data=command_data_receiver.message
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

    async def _atom_sensor_data(
        self,
        client: BleakClient,
        device: AirthingsDevice,
        sensors: dict[str, str | float | None],
        service: BleakGATTService,
    ) -> None:
        """Get sensor data from the device."""
        device.firmware = device.model.need_firmware_upgrade(
            self.device_info.sw_version
        )

        if device.firmware.need_firmware_upgrade:
            self.logger.warning(
                "The firmware for this device (%s) is not up to date, "
                "please update to %s or newer using the Airthings app.",
                self.device_info.address,
                device.firmware.required_version or "N/A",
            )

        connectivity_data = await self._create_decoder_and_fetch(
            client=client,
            service=service,
            url=AtomRequestPath.CONNECTIVITY_MODE,
        )
        if connectivity_data is not None:
            sensors.update(connectivity_data)

        sensor_data = await self._create_decoder_and_fetch(
            client=client,
            service=service,
            url=AtomRequestPath.LATEST_VALUES,
        )
        if sensor_data is not None:
            self._parse_sensor_data(
                device=device,
                sensors=sensors,
                sensor_data=sensor_data,
            )

    async def _create_decoder_and_fetch(
        self,
        client: BleakClient,
        service: BleakGATTService,
        url: AtomRequestPath,
    ) -> dict[str, float | str | None] | None:
        """Create decoder and fetch data."""
        decoder = AtomCommandDecode(url=url)
        command_data_receiver = decoder.make_data_receiver()

        atom_write = service.get_characteristic(COMMAND_UUID_ATOM)
        atom_notify = service.get_characteristic(COMMAND_UUID_ATOM_NOTIFY)

        if atom_write is None or atom_notify is None:
            raise ValueError("Missing characteristics for device")

        # Set up the notification handlers
        await client.start_notify(
            char_specifier=atom_notify, callback=command_data_receiver
        )

        # send command to this 'indicate' characteristic
        await client.write_gatt_char(atom_write, bytearray(decoder.cmd))
        # Wait for up to five seconds to see if a callback comes in.
        try:
            await command_data_receiver.wait_for_message(5)
        except asyncio.TimeoutError:
            self.logger.warning("Timeout getting command data.")

        data = decoder.decode_data(
            logger=self.logger,
            raw_data=command_data_receiver.message,
        )

        await client.stop_notify(atom_notify)

        return data

    def _parse_sensor_data(
        self,
        device: AirthingsDevice,
        sensors: dict[str, str | float | None],
        sensor_data: dict[str, float | str | None],
    ) -> None:
        """Parse sensor data from the device."""
        if sensor_data is not None:
            new_values: dict[str, float | str | None] = {}

            if (bat_data := sensor_data.get("BAT")) is not None:
                new_values["battery"] = device.model.battery_percentage(
                    float(bat_data) / 1000.0
                )

            if (lux := sensor_data.get("LUX")) is not None:
                new_values["lux"] = lux

            if (co2 := sensor_data.get("CO2")) is not None:
                new_values["co2"] = co2

            if (voc := sensor_data.get("VOC")) is not None:
                new_values["voc"] = voc

            if (hum := sensor_data.get("HUM")) is not None:
                new_values["humidity"] = float(hum) / 100.0

            if (temperature := sensor_data.get("TMP")) is not None:
                # Temperature reported as kelvin
                new_values["temperature"] = round(
                    float(temperature) / 100.0 - 273.15, 2
                )

            if (noise := sensor_data.get("NOI")) is not None:
                new_values["noise"] = noise

            if (pressure := sensor_data.get("PRS")) is not None:
                new_values["pressure"] = float(pressure) / (64 * 100)

            if (radon_1day_avg := sensor_data.get("R24")) is not None:
                new_values["radon_1day_avg"] = radon_1day_avg
                new_values["radon_1day_level"] = get_radon_level(float(radon_1day_avg))

            if (radon_week_avg := sensor_data.get("R7D")) is not None:
                new_values["radon_week_avg"] = radon_week_avg
                new_values["radon_week_level"] = get_radon_level(float(radon_week_avg))

            if (radon_month_avg := sensor_data.get("R30D")) is not None:
                new_values["radon_month_avg"] = radon_month_avg
                new_values["radon_month_level"] = get_radon_level(
                    float(radon_month_avg)
                )

            if (radon_year_avg := sensor_data.get("R1Y")) is not None:
                new_values["radon_year_avg"] = radon_year_avg
                new_values["radon_year_level"] = get_radon_level(float(radon_year_avg))

            self.logger.debug("Sensor values: %s", new_values)

            sensors.update(new_values)

    def _handle_disconnect(
        self, disconnect_future: asyncio.Future[bool], client: BleakClient
    ) -> None:
        """Handle disconnect from device."""
        self.logger.debug("Disconnected from %s", client.address)
        if not disconnect_future.done():
            disconnect_future.set_result(True)

    async def update_device(self, ble_device: BLEDevice) -> AirthingsDevice:
        """Connects to the device through BLE and retrieves relevant data"""
        # Try to abort early if the device name indicates it is not supported.
        # In some cases we only get the mac address, so we need to connect to
        # the device to get the name.
        if name := ble_device.name:
            if "Renew" in name or "View" in name:
                raise UnsupportedDeviceError(f"Model {name} is not supported")
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
                BleakClientWithServiceCache,
                ble_device,
                ble_device.address,
                disconnected_callback=partial(
                    self._handle_disconnect, disconnect_future
                ),
            )
        )
        try:
            async with (
                interrupt(
                    disconnect_future,
                    DisconnectedError,
                    f"Disconnected from {client.address}",
                ),
                asyncio.timeout(UPDATE_TIMEOUT),
            ):
                await self._get_device_characteristics(client, device)
                await self._get_service_characteristics(client, device)
        except BleakError as err:
            if "not found" in str(err):  # In future bleak this is a named exception
                # Clear the char cache since a char is likely
                # missing from the cache
                await client.clear_cache()
            raise
        except UnsupportedDeviceError:
            await client.disconnect()
            raise
        finally:
            await client.disconnect()

        return device
