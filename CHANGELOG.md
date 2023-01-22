# Changelog

<!--next-version-placeholder-->

## v0.5.5 (2023-01-22)
### Fix
* Update the notification receiver to wait until the full message is received before return ([#8](https://github.com/vincegio/airthings-ble/issues/8)) ([`67e3ff7`](https://github.com/vincegio/airthings-ble/commit/67e3ff743adcfed6494d79354f252d056d1d21d7))

## v0.5.4 (2023-01-17)
### Fix
* Properly disconnect when there is an exception reading device state ([#7](https://github.com/vincegio/airthings-ble/issues/7)) ([`3b8de60`](https://github.com/vincegio/airthings-ble/commit/3b8de60b7a13a5a174819404b9b51f66674847a5))

## v0.5.3 (2022-11-13)
### Fix
* Gracefully delete date_time ([#3](https://github.com/vincegio/airthings-ble/issues/3)) ([`e5ca63f`](https://github.com/vincegio/airthings-ble/commit/e5ca63f75044e4cb6f31d6b1ed55d2154f9acaa2))

## v0.5.2 (2022-09-29)
### Fix
* Fix version pinning for bleak-retry-connector ([`6a8982c`](https://github.com/vincegio/airthings-ble/commit/6a8982c87cfcfb37b8ea1f9bad878444cc025c0a))

## v0.5.1 (2022-09-10)
### Fix
* Fix incompability with home assistant package versionings ([`0949bd2`](https://github.com/vincegio/airthings-ble/commit/0949bd28c7495264be55da4b9f1997cae2b391e5))

## v0.5.0 (2022-08-28)
### Feature
* Change identifier to be serial number ([`13fd0bd`](https://github.com/vincegio/airthings-ble/commit/13fd0bda1bd544b8a3c7d39baa187d5b7127599a))

## v0.4.0 (2022-08-28)
### Feature
* Gracefully pass bleak exceptions during characteristics readings ([`29d38a7`](https://github.com/vincegio/airthings-ble/commit/29d38a754b0ad8a2390d7d17b626061e29f135ba))

## v0.3.0 (2022-08-24)
### Feature
* Add dataclass to AirthingsDevice ([`88e525a`](https://github.com/vincegio/airthings-ble/commit/88e525ae9e00ce707f316785538aedc0d7b9dcaa))

### Fix
* Properly parse rel_atm_pressure ([`8f32209`](https://github.com/vincegio/airthings-ble/commit/8f3220948e2e74f7957890c81ada04aa9925c196))

## v0.2.0 (2022-08-23)
### Feature
* Add device ident and address, make variables optional ([`0e1e80d`](https://github.com/vincegio/airthings-ble/commit/0e1e80d78c1a400c773e37d3982614d3c246b607))

## v0.1.0 (2022-08-22)
### Feature
* Add battery percentage ([`cb8f4b3`](https://github.com/vincegio/airthings-ble/commit/cb8f4b34506d8143cda0f9b3854da825829327e9))
