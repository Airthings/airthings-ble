from __future__ import annotations
import asyncio
from collections import namedtuple
from datetime import datetime

import struct
from logging import Logger
from uuid import UUID

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection
from bluetooth_sensor_state_data import BluetoothData
from home_assistant_bluetooth import BluetoothServiceInfo
from sensor_state_data import (
    SensorUpdate,
    SensorLibrary,
    DeviceClass,
    Units,
)

from .const import CHAR_UUID_DATETIME, CHAR_UUID_DEVICE_NAME, CHAR_UUID_FIRMWARE_REV, CHAR_UUID_HARDWARE_REV, CHAR_UUID_HUMIDITY, CHAR_UUID_ILLUMINANCE_ACCELEROMETER, CHAR_UUID_MANUFACTURER_NAME, CHAR_UUID_MODEL_NUMBER_STRING, CHAR_UUID_RADON_1DAYAVG, CHAR_UUID_RADON_LONG_TERM_AVG, CHAR_UUID_SERIAL_NUMBER_STRING, CHAR_UUID_TEMPERATURE, CHAR_UUID_WAVE_2_DATA, CHAR_UUID_WAVE_PLUS_DATA, CHAR_UUID_WAVEMINI_DATA, COMMAND_UUID, MFCT_ID


Characteristic = namedtuple('Characteristic', ['uuid', 'name', 'format'])

manufacturer_characteristics = Characteristic(CHAR_UUID_MANUFACTURER_NAME, 'manufacturer', "utf-8")
device_info_characteristics = [manufacturer_characteristics,
                               Characteristic(CHAR_UUID_SERIAL_NUMBER_STRING, 'serial_nr', "utf-8"),
                               Characteristic(CHAR_UUID_MODEL_NUMBER_STRING, 'model_nr', "utf-8"),
                               Characteristic(CHAR_UUID_DEVICE_NAME, 'device_name', "utf-8"),
                               Characteristic(CHAR_UUID_FIRMWARE_REV, 'firmware_rev', "utf-8"),
                               Characteristic(CHAR_UUID_HARDWARE_REV, 'hardware_rev', "utf-8")]

sensors_characteristics_uuid = [CHAR_UUID_DATETIME, CHAR_UUID_TEMPERATURE, CHAR_UUID_HUMIDITY, CHAR_UUID_RADON_1DAYAVG,
                                CHAR_UUID_RADON_LONG_TERM_AVG, CHAR_UUID_ILLUMINANCE_ACCELEROMETER,
                                CHAR_UUID_WAVE_PLUS_DATA,CHAR_UUID_WAVE_2_DATA,CHAR_UUID_WAVEMINI_DATA,
                                COMMAND_UUID]
sensors_characteristics_uuid_str = [str(x) for x in sensors_characteristics_uuid]

class BaseDecode:
    def __init__(self, name, format_type, scale):
        self.name = name
        self.format_type = format_type
        self.scale = scale

    def decode_data(self, raw_data):
        val = struct.unpack(
            self.format_type,
            raw_data)
        if len(val) == 1:
            res = val[0] * self.scale
        else:
            res = val
        return {self.name:res}


class WavePlussDecode(BaseDecode):
    def decode_data(self, raw_data):
        val = super().decode_data(raw_data)
        val = val[self.name]
        data = {}
        data['date_time'] = str(datetime.isoformat(datetime.now()))
        data['humidity'] = val[1]/2.0
        data['radon_1day_avg'] = val[4] if 0 <= val[4] <= 16383 else None
        data['radon_longterm_avg'] = val[5] if 0 <= val[5] <= 16383 else None
        data['temperature'] = val[6]/100.0
        data['rel_atm_pressure'] = val[7]/50.0
        data['co2'] = val[8]*1.0
        data['voc'] = val[9]*1.0
        return data


class Wave2Decode(BaseDecode):
    def decode_data(self, raw_data):
        val = super().decode_data(raw_data)
        val = val[self.name]
        data = {}
        data['date_time'] = str(datetime.isoformat(datetime.now()))
        data['humidity'] = val[1]/2.0
        data['radon_1day_avg'] = val[4] if 0 <= val[4] <= 16383 else None
        data['radon_longterm_avg'] = val[5] if 0 <= val[5] <= 16383 else None
        data['temperature'] = val[6]/100.0
        return data


class WaveMiniDecode(BaseDecode):
    def decode_data(self, raw_data):
        val = super().decode_data(raw_data)
        val = val[self.name]
        data = {}
        data['date_time'] = str(datetime.isoformat(datetime.now()))
        data['temperature'] = round( val[1]/100.0 - 273.15,2)
        data['humidity'] = val[3]/100.0
        data['voc'] = val[4]*1.0
        return data


class WaveDecodeDate(BaseDecode):
    def decode_data(self, raw_data):
        val = super().decode_data(raw_data)[self.name]
        data = {self.name:str(datetime(val[0], val[1], val[2], val[3], val[4], val[5]).isoformat())}
        return data


class WaveDecodeIluminAccel(BaseDecode):
    def decode_data(self, raw_data):
        val = super().decode_data(raw_data)[self.name]
        data = {}
        data['illuminance'] = str(val[0] * self.scale)
        data['accelerometer'] = str(val[1] * self.scale)
        return data


class CommandDecode:
    def __init__(self, name, format_type, cmd):
        self.name = name
        self.format_type = format_type
        self.cmd = cmd

    def decode_data(self, raw_data):
        if raw_data is None:
            return {}
        cmd = raw_data[0:1]
        if cmd != self.cmd:
            _LOGGER.warning("Result for Wrong command received, expected {} got {}".format(self.cmd.hex(), cmd.hex()))
            return {}
        
        if len(raw_data[2:]) != struct.calcsize(self.format_type):
            _LOGGER.debug("Wrong length data received ({}) verses expected ({})".format(len(cmd), struct.calcsize(self.format_type)))
            return {}
        val = struct.unpack(
            self.format_type,
            raw_data[2:])
        res = {}
        res['illuminance'] = val[2]
        #res['measurement_periods'] =  val[5]
        res['battery'] = val[17] / 1000.0

        return res

sensor_decoders = {str(CHAR_UUID_WAVE_PLUS_DATA):WavePlussDecode(name="Pluss", format_type='BBBBHHHHHHHH', scale=0),
                   str(CHAR_UUID_DATETIME):WaveDecodeDate(name="date_time", format_type='HBBBBB', scale=0),
                   str(CHAR_UUID_HUMIDITY):BaseDecode(name="humidity", format_type='H', scale=1.0/100.0),
                   str(CHAR_UUID_RADON_1DAYAVG):BaseDecode(name="radon_1day_avg", format_type='H', scale=1.0),
                   str(CHAR_UUID_RADON_LONG_TERM_AVG):BaseDecode(name="radon_longterm_avg", format_type='H', scale=1.0),
                   str(CHAR_UUID_ILLUMINANCE_ACCELEROMETER):WaveDecodeIluminAccel(name="illuminance_accelerometer", format_type='BB', scale=1.0),
                   str(CHAR_UUID_TEMPERATURE):BaseDecode(name="temperature", format_type='h', scale=1.0/100.0),
                   str(CHAR_UUID_WAVE_2_DATA):Wave2Decode(name="Wave2", format_type='<4B8H', scale=1.0),
                   str(CHAR_UUID_WAVEMINI_DATA):WaveMiniDecode(name="WaveMini", format_type='<HHHHHHLL', scale=1.0),}

command_decoders = {str(COMMAND_UUID):CommandDecode(name="Battery", format_type='<L12B6H', cmd=struct.pack('<B', 0x6d))}





def short_address(address: str) -> str:
    """Convert a Bluetooth address to a short address."""
    results = address.replace("-", ":").split(":")
    res = 'string'
    if len(results[-1]) == 2:
        return f"{results[-2].upper()}{results[-1].upper()}"
    return results[-1].upper()


def decode_temps(packet_value: int) -> float:
    """Decode potential negative temperatures."""
    # https://github.com/Thrilleratplay/GoveeWatcher/issues/2
    if packet_value & 0x800000:
        return float((packet_value ^ 0x800000) / -10000)
    return float(packet_value / 10000)


def decode_temps_probes(packet_value: int) -> float:
    """Filter potential negative temperatures."""
    if packet_value < 0:
        return 0.0
    return float(packet_value / 100)


class AirthingsBluetoothDeviceData(BluetoothData):
    """Data for Airthings BLE sensors."""
    def __init__(self, logger: Logger):
        super().__init__()
        self.logger = logger
        self._command_data = None
        self._event = None

    def _start_update(self, service_info: BluetoothServiceInfo) -> None:
        """Update from BLE advertisement data."""
        if not service_info.manufacturer_data[MFCT_ID]:
            return

        self.set_device_manufacturer("Airthings AS")
        # self.set_device_type("Wave Plus")
        # self.device_id = 0x0B48
        # self.set_title(f"test device 2 (Wave Plus)")
        # self.set_device_name(f"Big dick Wave Plus")

        # self.set_device_sw_version("420.0.0")



    def poll_needed(
        self, service_info: BluetoothServiceInfo, last_poll: float | None
    ) -> bool:
        """
        This is called every time we get a service_info for a device. It means the
        device is working and online. If 24 hours has passed, it may be a good
        time to poll the device.
        """
        return True
    def notification_handler(self, sender, data):
        self.logger.debug("Notification handler: {0}: {1}".format(sender, data))
        self._command_data = data
        self._event.set()

    async def async_poll(self, ble_device: BLEDevice) -> SensorUpdate:
        """
        Poll the device to retrieve any values we can't get from passive listening.
        """
        client = await establish_connection(
                BleakClient, ble_device, ble_device.address
            )
        try:
            for characteristic in device_info_characteristics:
                try:
                    data = await client.read_gatt_char(characteristic.uuid)
                    self.logger.debug("attr: %s %s", characteristic.name, data)
                    if characteristic.name == "hardware_rev":
                        self.set_device_hw_version(data.decode(characteristic.format))
                    elif characteristic.name == "firmware_rev": 
                        self.set_device_sw_version(data.decode(characteristic.format))
                except:
                    self.logger.exception("Error getting info")

            sensor_characteristics =  []
            svcs = await client.get_services()
            for service in svcs:
                for characteristic in service.characteristics:
                    if characteristic.uuid in sensors_characteristics_uuid_str and str(characteristic.uuid) in sensor_decoders:
                        data = await client.read_gatt_char(characteristic.uuid)
                        sensor_data = sensor_decoders[str(characteristic.uuid)].decode_data(data)                            
                        self.logger.debug("characteristic for: %s", sensor_data)
                        self.update_predefined_sensor(SensorLibrary.HUMIDITY__PERCENTAGE, sensor_data["humidity"])
                        self.update_predefined_sensor(SensorLibrary.TEMPERATURE__CELSIUS, sensor_data["temperature"])
                        self.update_sensor(
                            key=f"{DeviceClass.PRESSURE}_{Units.PRESSURE_MBAR}",
                            device_class=DeviceClass.PRESSURE,
                            native_value=sensor_data["rel_atm_pressure"],
                            native_unit_of_measurement=Units.PRESSURE_MBAR
                        )

                        self.update_sensor(
                            key="radon_1day_avg",
                            device_class="radon_1day_avg",                            native_value=sensor_data["radon_1day_avg"],
                            native_unit_of_measurement="Bq/m3"
                        )

                        self.update_sensor(
                            key="radon_longterm_avg",
                            device_class="radon_longterm_avg",
                            native_value=sensor_data["radon_longterm_avg"],
                            native_unit_of_measurement="Bq/m3"
                        )
                    
                    if str(characteristic.uuid) in command_decoders:
                        self._event = asyncio.Event()
                        # Set up the notification handlers
                        await client.start_notify(characteristic.uuid, self.notification_handler)
                        # send command to this 'indicate' characteristic
                        await client.write_gatt_char(characteristic.uuid, command_decoders[str(characteristic.uuid)].cmd)
                        # Wait for up to one second to see if a callblack comes in.
                        try:
                            await asyncio.wait_for(self._event.wait(), 1)
                        except asyncio.TimeoutError:
                            self.logger.warn("Timeout getting command data.")
                        if self._command_data is not None:
                            sensor_data = command_decoders[str(characteristic.uuid)].decode_data(self._command_data)
                            self.logger.debug("command: %s", sensor_data)
                            self._command_data = None
                        # Stop notification handler
                        await client.stop_notify(characteristic.uuid)
        finally:
            await client.disconnect()
       
        return self._finish_update()