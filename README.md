# airthings-ble

Library to control Airthings devices through BLE, primarily meant to be used in
the [Home Assistant integration](https://www.home-assistant.io/integrations/airthings_ble/). 

The integration supports the following devices:

- [Wave Plus](https://www.airthings.com/en/wave-plus)
- [Wave Mini](https://www.airthings.com/en/wave-mini)
- [Wave Radon](https://www.airthings.com/en/wave-radon)
- Wave Gen 1

Although some other devices have BLE capabilities, those devices use BLE for onboarding and configuration.
It is not possible to fetch sensor data using this library.

## Getting Started

Prerequisites:

- [Python](https://www.python.org/downloads/) with version 3.11 that is required by Home Assistant ([docs](https://developers.home-assistant.io/docs/development_environment?_highlight=python&_highlight=versi#manual-environment) or [reference](https://github.com/home-assistant/architecture/blob/master/adr/0002-minimum-supported-python-version.md))
- [Poetry](https://python-poetry.org/docs/#installation)

Install dependencies:

```bash
poetry install
```

Run tests:

```bash
poetry run pytest
```

See [this wiki page](https://github.com/Airthings/airthings-ble/wiki/Testing-with-Home-Assistant) for more details
on how to test the library with HA.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details. 