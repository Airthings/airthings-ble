from bluetooth_sensor_state_data import BluetoothServiceInfo, DeviceClass, SensorUpdate
from sensor_state_data import (
    DeviceKey,
    SensorDescription,
    SensorDeviceInfo,
    SensorValue,
    Units,
)

from airthings_ble.parser import GoveeBluetoothDeviceData

GVH5075_SERVICE_INFO = BluetoothServiceInfo(
    name="GVH5075_2762",
    address="61DE521B-F0BF-9F44-64D4-75BBE1738105",
    rssi=-63,
    manufacturer_data={
        60552: b"\x00\x03A\xc2d\x00L\x00\x02\x15INTELLI_ROCKS_HWPu\xf2\xff\x0c"
    },
    service_uuids=["0000ec88-0000-1000-8000-00805f9b34fb"],
    service_data={},
    source="local",
)
GVH5052_SERVICE_INFO = BluetoothServiceInfo(
    name="Govee_H5052_E81B",
    address="61DE521B-F0BF-9F44-64D4-75BBE1738105",
    rssi=-63,
    manufacturer_data={60552: b"\x00\x1c\x01\xa7\x14;\x00\x00\x02"},
    service_uuids=[
        "0000180a-0000-1000-8000-00805f9b34fb",
        "0000fef5-0000-1000-8000-00805f9b34fb",
        "0000ec88-0000-1000-8000-00805f9b34fb",
    ],
    service_data={},
    source="local",
)

GVH5177_SERVICE_INFO = BluetoothServiceInfo(
    name="GVH5177_2EC8",
    address="4125DDBA-2774-4851-9889-6AADDD4CAC3D",
    rssi=-56,
    manufacturer_data={
        1: b"\x01\x01\x036&dL\x00\x02\x15INTELLI_ROCKS_HWQw\xf2\xff\xc2"
    },
    service_uuids=["0000ec88-0000-1000-8000-00805f9b34fb"],
    service_data={},
    source="local",
)

GVH5184_SERVICE_INFO_1 = BluetoothServiceInfo(
    name="GVH5184_XXXX",
    address="4125DDBA-2774-4851-9889-6AADDD4CAC3D",
    rssi=-56,
    manufacturer_data={
        6966: b" \x01\x00\x01\x01\xe4\x01\x86\x0c\x1c\xff\xff\x86\n\xf0\xff\xff",
        76: b"\x02\x15INTELLI_ROCKS_HWPu\xf2\xff\x0c",
    },
    service_uuids=["00008451-0000-1000-8000-00805f9b34fb"],
    service_data={},
    source="local",
)
GVH5184_SERVICE_INFO_2 = BluetoothServiceInfo(
    name="GVH5184_XXXX",
    address="4125DDBA-2774-4851-9889-6AADDD4CAC3D",
    rssi=-56,
    manufacturer_data={
        6966: b" \x01\x00\x01\x01\xe4\x02\x86\x0b\xb8\xff\xff\x86\x0bT\xff\xff",
        76: b"\x02\x15INTELLI_ROCKS_HWPu\xf2\xff\x0c",
    },
    service_uuids=["00008451-0000-1000-8000-00805f9b34fb"],
    service_data={},
    source="local",
)
GVH5185_SERVICE_INFO = BluetoothServiceInfo(
    name="GVH5185_2EC8",
    address="4125DDBA-2774-4851-9889-6AADDD4CAC3D",
    rssi=-56,
    manufacturer_data={
        18994: b"\x87\x01\x00\x01\x01\xe4\xc1f\x084\xff\xff\xff\xff"
        b"\x084\xff\xff\xff\xffL\x00\x02\x15INTELLI_ROCKS_HWPu\xf2\xff\x0c"
    },
    service_uuids=["00008551-0000-1000-8000-00805f9b34fb"],
    service_data={},
    source="local",
)

GVH5185_VARIANT_SERVICE_INFO = BluetoothServiceInfo(
    name="GVH5185_VAR2",
    address="4125DDBA-2774-4851-9889-6AADDD4CAC3D",
    rssi=-56,
    manufacturer_data={
        818: b"T\x01\x00\x01\x01\xe4\xc1f\t\xc4\xff\xff\xff\xff\t\xc4\xff\xff\xff\xff",
        76: b"\x02\x15INTELLI_ROCKS_HWPu\xf2\xff\x0c",
    },
    service_uuids=["00008551-0000-1000-8000-00805f9b34fb"],
    service_data={},
    source="local",
)


GVH5183_SERVICE_INFO = BluetoothServiceInfo(
    name="GVH5183_2EC8",
    address="4125DDBA-2774-4851-9889-6AADDD4CAC3D",
    rssi=-56,
    manufacturer_data={
        26589: b"\xef\x01\x00\x01\x01\xe4\x01\x80\x084\xff\xff\x00"
        b"\x00L\x00\x02\x15INTELLI_ROCKS_HWPu\xf2\xff\x0c"
    },
    service_uuids=["00008351-0000-1000-8000-00805f9b34fb"],
    service_data={},
    source="local",
)
GVH5181_SERVICE_INFO = BluetoothServiceInfo(
    name="GVH5181_2EC8",
    address="4125DDBA-2774-4851-9889-6AADDD4CAC3D",
    rssi=-56,
    manufacturer_data={
        14474: b"\xd8\x01\x00\x01\x01\xe4\x01\x86\x08\x98\x1d"
        b"\x10\x00\x00L\x00\x02\x15INTELLI_ROCKS_HWPu\xf2\xff\x0c"
    },
    service_uuids=["00008151-0000-1000-8000-00805f9b34fb"],
    service_data={},
    source="local",
)
GVH5181_VARIANT_SERVICE_INFO = BluetoothServiceInfo(
    name="GVH5181_2EC8",
    address="4125DDBA-2774-4851-9889-6AADDD4CAC3D",
    rssi=-56,
    manufacturer_data={
        59970: b"\xba\x01\x00\x01\x01d\x00\x06\xff\xff\x1c\xe8\x00\x00",
        76: b"\x02\x15INTELLI_ROCKS_HWPu\xf2\xff\x0c",
    },
    service_uuids=["00008151-0000-1000-8000-00805f9b34fb"],
    service_data={},
    source="local",
)
GVH5181_VARIANT_SERVICE_INFO_2 = BluetoothServiceInfo(
    name="GVH5181_2EC8",
    address="4125DDBA-2774-4851-9889-6AADDD4CAC3D",
    rssi=-56,
    manufacturer_data={
        59970: b"\xba\x01\x00\x01\x01d\x00\x86\n(\x1c\xe8\x00\x00",
        76: b"\x02\x15INTELLI_ROCKS_HWPu\xf2\xff\x0c",
    },
    service_uuids=["00008151-0000-1000-8000-00805f9b34fb"],
    service_data={},
    source="local",
)
GVH5182_SERVICE_INFO = BluetoothServiceInfo(
    name="F34DC3CB-9CCF-336F-3CB1-3C6F525509E6",
    address="F34DC3CB-9CCF-336F-3CB1-3C6F525509E6",
    rssi=-56,
    manufacturer_data={
        10032: b"c\x01\x00\x01\x01\xe4\x01\x01\xff\xff\x12\x03\x01"
        b"\xff\xff\x00\x00L\x00\x02\x15INTELLI_ROCKS_HWPu\xf2\xff\x0c"
    },
    service_uuids=["00008251-0000-1000-8000-00805f9b34fb"],
    service_data={},
    source="local",
)
GVH5179_SERVICE_INFO = BluetoothServiceInfo(
    name="Govee_H5179_3CD5",
    address="10F1A254-16A5-9F35-BE40-7034507A6967",
    rssi=-50,
    manufacturer_data={34817: b"\xec\x00\x01\x01\n\n\xa4\x06d"},
    service_data={},
    service_uuids=[
        "0000180a-0000-1000-8000-00805f9b34fb",
        "0000fef5-0000-1000-8000-00805f9b34fb",
        "0000ec88-0000-1000-8000-00805f9b34fb",
    ],
    source="local",
)
GVH5074_SERVICE_INFO = BluetoothServiceInfo(
    name="Govee_H5074_5FF4",
    address="99214D75-854A-E52B-704D-C5C9B7F5D59C",
    rssi=-67,
    manufacturer_data={
        60552: b"\x00\xe6\t\xbc\x12d\x02",
        76: b"\x02\x15INTELLI_ROCKS_HWPu\xf2\xff\xc2",
    },
    service_data={},
    service_uuids=["0000ec88-0000-1000-8000-00805f9b34fb"],
    source="local",
)


def test_can_create():
    GoveeBluetoothDeviceData()


def test_gvh5052():
    parser = GoveeBluetoothDeviceData()
    service_info = GVH5052_SERVICE_INFO
    result = parser.update(service_info)
    assert result == SensorUpdate(
        title=None,
        devices={
            None: SensorDeviceInfo(
                name="H5052_E81B",
                model="H5052",
                manufacturer="Govee",
                sw_version=None,
                hw_version=None,
            )
        },
        entity_descriptions={
            DeviceKey(key="temperature", device_id=None): SensorDescription(
                device_key=DeviceKey(key="temperature", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(key="humidity", device_id=None): SensorDescription(
                device_key=DeviceKey(key="humidity", device_id=None),
                device_class=DeviceClass.HUMIDITY,
                native_unit_of_measurement=Units.PERCENTAGE,
            ),
            DeviceKey(key="battery", device_id=None): SensorDescription(
                device_key=DeviceKey(key="battery", device_id=None),
                device_class=DeviceClass.BATTERY,
                native_unit_of_measurement=Units.PERCENTAGE,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorDescription(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                device_class=DeviceClass.SIGNAL_STRENGTH,
                native_unit_of_measurement=Units.SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            ),
        },
        entity_values={
            DeviceKey(key="temperature", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature", device_id=None),
                name="Temperature",
                native_value=2.84,
            ),
            DeviceKey(key="humidity", device_id=None): SensorValue(
                device_key=DeviceKey(key="humidity", device_id=None),
                name="Humidity",
                native_value=52.87,
            ),
            DeviceKey(key="battery", device_id=None): SensorValue(
                device_key=DeviceKey(key="battery", device_id=None),
                name="Battery",
                native_value=59,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorValue(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                name="Signal Strength",
                native_value=-63,
            ),
        },
    )


def test_gvh5075():
    parser = GoveeBluetoothDeviceData()
    service_info = GVH5075_SERVICE_INFO
    result = parser.update(service_info)
    assert result == SensorUpdate(
        title=None,
        devices={
            None: SensorDeviceInfo(
                name="H5075_2762",
                model="H5072/H5075",
                manufacturer="Govee",
                sw_version=None,
                hw_version=None,
            )
        },
        entity_descriptions={
            DeviceKey(key="temperature", device_id=None): SensorDescription(
                device_key=DeviceKey(key="temperature", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(key="humidity", device_id=None): SensorDescription(
                device_key=DeviceKey(key="humidity", device_id=None),
                device_class=DeviceClass.HUMIDITY,
                native_unit_of_measurement=Units.PERCENTAGE,
            ),
            DeviceKey(key="battery", device_id=None): SensorDescription(
                device_key=DeviceKey(key="battery", device_id=None),
                device_class=DeviceClass.BATTERY,
                native_unit_of_measurement=Units.PERCENTAGE,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorDescription(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                device_class=DeviceClass.SIGNAL_STRENGTH,
                native_unit_of_measurement=Units.SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            ),
        },
        entity_values={
            DeviceKey(key="temperature", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature", device_id=None),
                name="Temperature",
                native_value=21.3442,
            ),
            DeviceKey(key="humidity", device_id=None): SensorValue(
                device_key=DeviceKey(key="humidity", device_id=None),
                name="Humidity",
                native_value=44.2,
            ),
            DeviceKey(key="battery", device_id=None): SensorValue(
                device_key=DeviceKey(key="battery", device_id=None),
                name="Battery",
                native_value=100,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorValue(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                name="Signal Strength",
                native_value=-63,
            ),
        },
    )


def test_gvh5177():
    parser = GoveeBluetoothDeviceData()
    service_info = GVH5177_SERVICE_INFO
    result = parser.update(service_info)
    assert result == SensorUpdate(
        title=None,
        devices={
            None: SensorDeviceInfo(
                name="H5177_2EC8",
                model="H5101/H5102/H5177",
                manufacturer="Govee",
                sw_version=None,
                hw_version=None,
            )
        },
        entity_descriptions={
            DeviceKey(key="temperature", device_id=None): SensorDescription(
                device_key=DeviceKey(key="temperature", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(key="humidity", device_id=None): SensorDescription(
                device_key=DeviceKey(key="humidity", device_id=None),
                device_class=DeviceClass.HUMIDITY,
                native_unit_of_measurement=Units.PERCENTAGE,
            ),
            DeviceKey(key="battery", device_id=None): SensorDescription(
                device_key=DeviceKey(key="battery", device_id=None),
                device_class=DeviceClass.BATTERY,
                native_unit_of_measurement=Units.PERCENTAGE,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorDescription(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                device_class=DeviceClass.SIGNAL_STRENGTH,
                native_unit_of_measurement=Units.SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            ),
        },
        entity_values={
            DeviceKey(key="temperature", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature", device_id=None),
                name="Temperature",
                native_value=21.047,
            ),
            DeviceKey(key="humidity", device_id=None): SensorValue(
                device_key=DeviceKey(key="humidity", device_id=None),
                name="Humidity",
                native_value=47.0,
            ),
            DeviceKey(key="battery", device_id=None): SensorValue(
                device_key=DeviceKey(key="battery", device_id=None),
                name="Battery",
                native_value=100,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorValue(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                name="Signal Strength",
                native_value=-56,
            ),
        },
    )


def test_gvh5184_packet_type_1():
    parser = GoveeBluetoothDeviceData()
    result = parser.update(GVH5184_SERVICE_INFO_1)
    assert result == SensorUpdate(
        title=None,
        devices={
            None: SensorDeviceInfo(
                name="H5184 6AADDD4CAC3D",
                model="H5184",
                manufacturer="Govee",
                sw_version=None,
                hw_version=None,
            )
        },
        entity_descriptions={
            DeviceKey(key="temperature_probe_1", device_id=None): SensorDescription(
                device_key=DeviceKey(key="temperature_probe_1", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(
                key="temperature_alarm_probe_1", device_id=None
            ): SensorDescription(
                device_key=DeviceKey(key="temperature_alarm_probe_1", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(key="temperature_probe_2", device_id=None): SensorDescription(
                device_key=DeviceKey(key="temperature_probe_2", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(
                key="temperature_alarm_probe_2", device_id=None
            ): SensorDescription(
                device_key=DeviceKey(key="temperature_alarm_probe_2", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorDescription(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                device_class=DeviceClass.SIGNAL_STRENGTH,
                native_unit_of_measurement=Units.SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            ),
        },
        entity_values={
            DeviceKey(key="temperature_probe_1", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_probe_1", device_id=None),
                name="Temperature Probe 1",
                native_value=31.0,
            ),
            DeviceKey(key="temperature_alarm_probe_1", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_alarm_probe_1", device_id=None),
                name="Temperature Alarm Probe 1",
                native_value=0.0,
            ),
            DeviceKey(key="temperature_probe_2", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_probe_2", device_id=None),
                name="Temperature Probe 2",
                native_value=28.0,
            ),
            DeviceKey(key="temperature_alarm_probe_2", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_alarm_probe_2", device_id=None),
                name="Temperature Alarm Probe 2",
                native_value=0.0,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorValue(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                name="Signal Strength",
                native_value=-56,
            ),
        },
    )


def test_gvh5184_packet_type_2():
    parser = GoveeBluetoothDeviceData()
    result = parser.update(GVH5184_SERVICE_INFO_2)
    assert result == SensorUpdate(
        title=None,
        devices={
            None: SensorDeviceInfo(
                name="H5184 6AADDD4CAC3D",
                model="H5184",
                manufacturer="Govee",
                sw_version=None,
                hw_version=None,
            )
        },
        entity_descriptions={
            DeviceKey(key="temperature_probe_3", device_id=None): SensorDescription(
                device_key=DeviceKey(key="temperature_probe_3", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(
                key="temperature_alarm_probe_3", device_id=None
            ): SensorDescription(
                device_key=DeviceKey(key="temperature_alarm_probe_3", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(key="temperature_probe_4", device_id=None): SensorDescription(
                device_key=DeviceKey(key="temperature_probe_4", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(
                key="temperature_alarm_probe_4", device_id=None
            ): SensorDescription(
                device_key=DeviceKey(key="temperature_alarm_probe_4", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorDescription(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                device_class=DeviceClass.SIGNAL_STRENGTH,
                native_unit_of_measurement=Units.SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            ),
        },
        entity_values={
            DeviceKey(key="temperature_probe_3", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_probe_3", device_id=None),
                name="Temperature Probe 3",
                native_value=30.0,
            ),
            DeviceKey(key="temperature_alarm_probe_3", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_alarm_probe_3", device_id=None),
                name="Temperature Alarm Probe 3",
                native_value=0.0,
            ),
            DeviceKey(key="temperature_probe_4", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_probe_4", device_id=None),
                name="Temperature Probe 4",
                native_value=29.0,
            ),
            DeviceKey(key="temperature_alarm_probe_4", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_alarm_probe_4", device_id=None),
                name="Temperature Alarm Probe 4",
                native_value=0.0,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorValue(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                name="Signal Strength",
                native_value=-56,
            ),
        },
    )


def test_gvh5185():
    parser = GoveeBluetoothDeviceData()
    service_info = GVH5185_SERVICE_INFO
    result = parser.update(service_info)
    assert result == SensorUpdate(
        title=None,
        devices={
            None: SensorDeviceInfo(
                name="H5185 6AADDD4CAC3D",
                model="H5185",
                manufacturer="Govee",
                sw_version=None,
                hw_version=None,
            )
        },
        entity_descriptions={
            DeviceKey(key="temperature_probe_1", device_id=None): SensorDescription(
                device_key=DeviceKey(key="temperature_probe_1", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(
                key="temperature_alarm_probe_1", device_id=None
            ): SensorDescription(
                device_key=DeviceKey(key="temperature_alarm_probe_1", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(key="temperature_probe_2", device_id=None): SensorDescription(
                device_key=DeviceKey(key="temperature_probe_2", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(
                key="temperature_alarm_probe_2", device_id=None
            ): SensorDescription(
                device_key=DeviceKey(key="temperature_alarm_probe_2", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorDescription(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                device_class=DeviceClass.SIGNAL_STRENGTH,
                native_unit_of_measurement=Units.SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            ),
        },
        entity_values={
            DeviceKey(key="temperature_probe_1", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_probe_1", device_id=None),
                name="Temperature Probe 1",
                native_value=21.0,
            ),
            DeviceKey(key="temperature_alarm_probe_1", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_alarm_probe_1", device_id=None),
                name="Temperature Alarm Probe 1",
                native_value=0.0,
            ),
            DeviceKey(key="temperature_probe_2", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_probe_2", device_id=None),
                name="Temperature Probe 2",
                native_value=21.0,
            ),
            DeviceKey(key="temperature_alarm_probe_2", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_alarm_probe_2", device_id=None),
                name="Temperature Alarm Probe 2",
                native_value=0.0,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorValue(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                name="Signal Strength",
                native_value=-56,
            ),
        },
    )


def test_gvh5185_variant():
    parser = GoveeBluetoothDeviceData()
    service_info = GVH5185_VARIANT_SERVICE_INFO
    result = parser.update(service_info)
    assert result == SensorUpdate(
        title=None,
        devices={
            None: SensorDeviceInfo(
                name="H5185 6AADDD4CAC3D",
                model="H5185",
                manufacturer="Govee",
                sw_version=None,
                hw_version=None,
            )
        },
        entity_descriptions={
            DeviceKey(
                key="temperature_alarm_probe_2", device_id=None
            ): SensorDescription(
                device_key=DeviceKey(key="temperature_alarm_probe_2", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(
                key="temperature_alarm_probe_1", device_id=None
            ): SensorDescription(
                device_key=DeviceKey(key="temperature_alarm_probe_1", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(key="temperature_probe_1", device_id=None): SensorDescription(
                device_key=DeviceKey(key="temperature_probe_1", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorDescription(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                device_class=DeviceClass.SIGNAL_STRENGTH,
                native_unit_of_measurement=Units.SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            ),
            DeviceKey(key="temperature_probe_2", device_id=None): SensorDescription(
                device_key=DeviceKey(key="temperature_probe_2", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
        },
        entity_values={
            DeviceKey(key="temperature_alarm_probe_2", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_alarm_probe_2", device_id=None),
                name="Temperature " "Alarm " "Probe " "2",
                native_value=0.0,
            ),
            DeviceKey(key="temperature_alarm_probe_1", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_alarm_probe_1", device_id=None),
                name="Temperature " "Alarm " "Probe " "1",
                native_value=0.0,
            ),
            DeviceKey(key="temperature_probe_1", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_probe_1", device_id=None),
                name="Temperature " "Probe " "1",
                native_value=25.0,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorValue(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                name="Signal " "Strength",
                native_value=-56,
            ),
            DeviceKey(key="temperature_probe_2", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_probe_2", device_id=None),
                name="Temperature " "Probe " "2",
                native_value=25.0,
            ),
        },
    )


def test_gvh5183():
    parser = GoveeBluetoothDeviceData()
    service_info = GVH5183_SERVICE_INFO
    result = parser.update(service_info)
    assert result == SensorUpdate(
        title=None,
        devices={
            None: SensorDeviceInfo(
                name="H5183 6AADDD4CAC3D",
                model="H5183",
                manufacturer="Govee",
                sw_version=None,
                hw_version=None,
            )
        },
        entity_descriptions={
            DeviceKey(key="temperature_probe_1", device_id=None): SensorDescription(
                device_key=DeviceKey(key="temperature_probe_1", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(
                key="temperature_alarm_probe_1", device_id=None
            ): SensorDescription(
                device_key=DeviceKey(key="temperature_alarm_probe_1", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorDescription(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                device_class=DeviceClass.SIGNAL_STRENGTH,
                native_unit_of_measurement=Units.SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            ),
        },
        entity_values={
            DeviceKey(key="temperature_probe_1", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_probe_1", device_id=None),
                name="Temperature Probe 1",
                native_value=21.0,
            ),
            DeviceKey(key="temperature_alarm_probe_1", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_alarm_probe_1", device_id=None),
                name="Temperature Alarm Probe 1",
                native_value=0.0,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorValue(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                name="Signal Strength",
                native_value=-56,
            ),
        },
    )


def test_gvh5181():
    parser = GoveeBluetoothDeviceData()
    service_info = GVH5181_SERVICE_INFO
    result = parser.update(service_info)
    assert result == SensorUpdate(
        title=None,
        devices={
            None: SensorDeviceInfo(
                name="H5181 6AADDD4CAC3D",
                model="H5181",
                manufacturer="Govee",
                sw_version=None,
                hw_version=None,
            )
        },
        entity_descriptions={
            DeviceKey(key="temperature_probe_1", device_id=None): SensorDescription(
                device_key=DeviceKey(key="temperature_probe_1", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(
                key="temperature_alarm_probe_1", device_id=None
            ): SensorDescription(
                device_key=DeviceKey(key="temperature_alarm_probe_1", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorDescription(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                device_class=DeviceClass.SIGNAL_STRENGTH,
                native_unit_of_measurement=Units.SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            ),
        },
        entity_values={
            DeviceKey(key="temperature_probe_1", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_probe_1", device_id=None),
                name="Temperature Probe 1",
                native_value=22.0,
            ),
            DeviceKey(key="temperature_alarm_probe_1", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_alarm_probe_1", device_id=None),
                name="Temperature Alarm Probe 1",
                native_value=74.4,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorValue(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                name="Signal Strength",
                native_value=-56,
            ),
        },
    )


def test_gvh5181_variant():
    parser = GoveeBluetoothDeviceData()
    service_info = GVH5181_VARIANT_SERVICE_INFO
    result = parser.update(service_info)
    assert result == SensorUpdate(
        title=None,
        devices={
            None: SensorDeviceInfo(
                name="H5181 6AADDD4CAC3D",
                model="H5181",
                manufacturer="Govee",
                sw_version=None,
                hw_version=None,
            )
        },
        entity_descriptions={
            DeviceKey(key="temperature_probe_1", device_id=None): SensorDescription(
                device_key=DeviceKey(key="temperature_probe_1", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(
                key="temperature_alarm_probe_1", device_id=None
            ): SensorDescription(
                device_key=DeviceKey(key="temperature_alarm_probe_1", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorDescription(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                device_class=DeviceClass.SIGNAL_STRENGTH,
                native_unit_of_measurement=Units.SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            ),
        },
        entity_values={
            DeviceKey(key="temperature_probe_1", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_probe_1", device_id=None),
                name="Temperature Probe 1",
                native_value=0.0,
            ),
            DeviceKey(key="temperature_alarm_probe_1", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_alarm_probe_1", device_id=None),
                name="Temperature Alarm Probe 1",
                native_value=74.0,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorValue(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                name="Signal Strength",
                native_value=-56,
            ),
        },
    )


def test_gvh5181_variant_2():
    parser = GoveeBluetoothDeviceData()
    service_info = GVH5181_VARIANT_SERVICE_INFO_2
    result = parser.update(service_info)
    assert result == SensorUpdate(
        title=None,
        devices={
            None: SensorDeviceInfo(
                name="H5181 6AADDD4CAC3D",
                model="H5181",
                manufacturer="Govee",
                sw_version=None,
                hw_version=None,
            )
        },
        entity_descriptions={
            DeviceKey(key="temperature_probe_1", device_id=None): SensorDescription(
                device_key=DeviceKey(key="temperature_probe_1", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(
                key="temperature_alarm_probe_1", device_id=None
            ): SensorDescription(
                device_key=DeviceKey(key="temperature_alarm_probe_1", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorDescription(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                device_class=DeviceClass.SIGNAL_STRENGTH,
                native_unit_of_measurement=Units.SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            ),
        },
        entity_values={
            DeviceKey(key="temperature_probe_1", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_probe_1", device_id=None),
                name="Temperature Probe 1",
                native_value=26.0,
            ),
            DeviceKey(key="temperature_alarm_probe_1", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_alarm_probe_1", device_id=None),
                name="Temperature Alarm Probe 1",
                native_value=74.0,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorValue(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                name="Signal Strength",
                native_value=-56,
            ),
        },
    )


def test_gvh5182():
    parser = GoveeBluetoothDeviceData()
    service_info = GVH5182_SERVICE_INFO
    result = parser.update(service_info)
    assert result == SensorUpdate(
        title=None,
        devices={
            None: SensorDeviceInfo(
                name="H5182 3C6F525509E6",
                model="H5182",
                manufacturer="Govee",
                sw_version=None,
                hw_version=None,
            )
        },
        entity_descriptions={
            DeviceKey(key="temperature_probe_1", device_id=None): SensorDescription(
                device_key=DeviceKey(key="temperature_probe_1", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(
                key="temperature_alarm_probe_1", device_id=None
            ): SensorDescription(
                device_key=DeviceKey(key="temperature_alarm_probe_1", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(key="temperature_probe_2", device_id=None): SensorDescription(
                device_key=DeviceKey(key="temperature_probe_2", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(
                key="temperature_alarm_probe_2", device_id=None
            ): SensorDescription(
                device_key=DeviceKey(key="temperature_alarm_probe_2", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorDescription(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                device_class=DeviceClass.SIGNAL_STRENGTH,
                native_unit_of_measurement=Units.SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            ),
        },
        entity_values={
            DeviceKey(key="temperature_probe_1", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_probe_1", device_id=None),
                name="Temperature Probe 1",
                native_value=0.0,
            ),
            DeviceKey(key="temperature_alarm_probe_1", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_alarm_probe_1", device_id=None),
                name="Temperature Alarm Probe 1",
                native_value=46.11,
            ),
            DeviceKey(key="temperature_probe_2", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_probe_2", device_id=None),
                name="Temperature Probe 2",
                native_value=0.0,
            ),
            DeviceKey(key="temperature_alarm_probe_2", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature_alarm_probe_2", device_id=None),
                name="Temperature Alarm Probe 2",
                native_value=0.0,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorValue(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                name="Signal Strength",
                native_value=-56,
            ),
        },
    )


def test_gvh5179():
    parser = GoveeBluetoothDeviceData()
    service_info = GVH5179_SERVICE_INFO
    result = parser.update(service_info)
    assert result == SensorUpdate(
        title=None,
        devices={
            None: SensorDeviceInfo(
                name="H5179_3CD5",
                model="H5179",
                manufacturer="Govee",
                sw_version=None,
                hw_version=None,
            )
        },
        entity_descriptions={
            DeviceKey(key="temperature", device_id=None): SensorDescription(
                device_key=DeviceKey(key="temperature", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(key="humidity", device_id=None): SensorDescription(
                device_key=DeviceKey(key="humidity", device_id=None),
                device_class=DeviceClass.HUMIDITY,
                native_unit_of_measurement=Units.PERCENTAGE,
            ),
            DeviceKey(key="battery", device_id=None): SensorDescription(
                device_key=DeviceKey(key="battery", device_id=None),
                device_class=DeviceClass.BATTERY,
                native_unit_of_measurement=Units.PERCENTAGE,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorDescription(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                device_class=DeviceClass.SIGNAL_STRENGTH,
                native_unit_of_measurement=Units.SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            ),
        },
        entity_values={
            DeviceKey(key="temperature", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature", device_id=None),
                name="Temperature",
                native_value=25.7,
            ),
            DeviceKey(key="humidity", device_id=None): SensorValue(
                device_key=DeviceKey(key="humidity", device_id=None),
                name="Humidity",
                native_value=17.0,
            ),
            DeviceKey(key="battery", device_id=None): SensorValue(
                device_key=DeviceKey(key="battery", device_id=None),
                name="Battery",
                native_value=100,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorValue(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                name="Signal Strength",
                native_value=-50,
            ),
        },
    )


def test_gvh5074():
    parser = GoveeBluetoothDeviceData()
    service_info = GVH5074_SERVICE_INFO
    result = parser.update(service_info)
    assert result == SensorUpdate(
        title=None,
        devices={
            None: SensorDeviceInfo(
                name="H5074_5FF4",
                model="H5074",
                manufacturer="Govee",
                sw_version=None,
                hw_version=None,
            )
        },
        entity_descriptions={
            DeviceKey(key="temperature", device_id=None): SensorDescription(
                device_key=DeviceKey(key="temperature", device_id=None),
                device_class=DeviceClass.TEMPERATURE,
                native_unit_of_measurement=Units.TEMP_CELSIUS,
            ),
            DeviceKey(key="humidity", device_id=None): SensorDescription(
                device_key=DeviceKey(key="humidity", device_id=None),
                device_class=DeviceClass.HUMIDITY,
                native_unit_of_measurement=Units.PERCENTAGE,
            ),
            DeviceKey(key="battery", device_id=None): SensorDescription(
                device_key=DeviceKey(key="battery", device_id=None),
                device_class=DeviceClass.BATTERY,
                native_unit_of_measurement=Units.PERCENTAGE,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorDescription(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                device_class=DeviceClass.SIGNAL_STRENGTH,
                native_unit_of_measurement=Units.SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            ),
        },
        entity_values={
            DeviceKey(key="temperature", device_id=None): SensorValue(
                device_key=DeviceKey(key="temperature", device_id=None),
                name="Temperature",
                native_value=25.34,
            ),
            DeviceKey(key="humidity", device_id=None): SensorValue(
                device_key=DeviceKey(key="humidity", device_id=None),
                name="Humidity",
                native_value=47.96,
            ),
            DeviceKey(key="battery", device_id=None): SensorValue(
                device_key=DeviceKey(key="battery", device_id=None),
                name="Battery",
                native_value=100,
            ),
            DeviceKey(key="signal_strength", device_id=None): SensorValue(
                device_key=DeviceKey(key="signal_strength", device_id=None),
                name="Signal Strength",
                native_value=-67,
            ),
        },
    )
