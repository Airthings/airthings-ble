# airthings-ble (label check test, do not merge)

Library to control Airthings devices through BLE, primarily meant to be used in
the [Home Assistant integration](https://www.home-assistant.io/integrations/airthings_ble/).

## Supported devices

This library supports the following Airthings devices:

- [Corentium Home 2](https://www.airthings.com/products/corentium-home-2)
- [Wave Enhance](https://www.airthings.com/wave-enhance)
- Wave Gen 1
- [Wave Mini](https://www.airthings.com/wave-mini)
- [Wave Plus](https://www.airthings.com/wave-plus)
- [Wave Radon](https://www.airthings.com/wave-radon)

## Unsupported devices
Although some other devices have BLE capabilities, they use BLE only for onboarding and configuration. It is **not** possible to fetch sensor data using this library from, for example:

-	Hub
-	[Renew](https://www.airthings.com/renew)
-	[View Plus](https://www.airthings.com/view-plus)
-	View Pollution
-	[View Radon](https://www.airthings.com/view-radon)

## Getting Started

Prerequisites:

- [Python](https://www.python.org/downloads/) 3.12 or newer. CI tests 3.12, 3.13 and 3.14; Home Assistant itself requires 3.14 ([docs](https://developers.home-assistant.io/docs/development_environment#manual-environment) or [reference](https://github.com/home-assistant/architecture/blob/master/adr/0002-minimum-supported-python-version.md))
- [Poetry](https://python-poetry.org/docs/#installation)

Install dependencies:

```bash
poetry install
```

Run tests:

```bash
poetry run pytest
```

Run the same checks as CI:

```bash
poetry run black --check airthings_ble
poetry run pylint airthings_ble
poetry run mypy airthings_ble
```

See [this wiki page](https://github.com/Airthings/airthings-ble/wiki/Testing-with-Home-Assistant) for more details
on how to test the library with HA.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
