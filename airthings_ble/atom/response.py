from logging import Logger
from typing import Any, cast

import cbor2
from airthings_ble.atom.request import AtomRequestPath
from airthings_ble.connectivity_mode import AirthingsConnectivityMode
from airthings_ble.const import CONNECTIVITY_MODE


class AtomResponse:
    """Response for Airthings BLE Atom API"""

    _header = bytearray.fromhex("1001000345")
    response: bytes | bytearray
    random_bytes: bytes
    path: AtomRequestPath

    def __init__(
        self,
        logger: Logger,
        response: bytes | bytearray | None,
        random_bytes: bytes,
        path: AtomRequestPath,
    ) -> None:
        self.logger = logger
        if response is None:
            raise ValueError("Response cannot be None")
        self.response = response
        self.random_bytes = random_bytes
        self.path = path

    @staticmethod
    def _loads(data: bytes | bytearray) -> object:
        try:
            return cbor2.loads(data)
        except cbor2.CBORError as err:
            raise ValueError("Invalid CBOR data") from err

    def parse(self) -> dict[str, float | str | None] | None:
        if self.response[0:5] != self._header:
            self.logger.error(
                "Invalid response header, expected %s, but got %s",
                self._header.hex(),
                self.response[0:5].hex(),
            )
            raise ValueError("Invalid response header")

        if self.response[5:7] != self.random_bytes:
            self.logger.debug(
                "Invalid response checksum, expected %s, but got %s",
                self.random_bytes.hex(),
                self.response[5:7].hex(),
            )
            raise ValueError("Invalid response checksum")

        if len(self.response) < 9:
            raise ValueError("Response too short")

        if self.response[7] != 0x81:
            self.logger.debug(
                "Invalid response type, expected 81, but got %s", self.response[7]
            )
            raise ValueError("Invalid response type")

        if self.response[8] != 0xA2:
            self.logger.debug(
                "Invalid response array length, expected 2, but got %s",
                self.response[8],
            )
            raise ValueError("Invalid response array length")

        data_bytes = self.response[7:]
        decoded_data = cast(list[dict[int, Any]], self._loads(data_bytes))

        if path := decoded_data[0].get(0):
            if path != self.path.value:
                self.logger.error(
                    "Response path does not match request path, expected %s but got %s",
                    self.path.value,
                    path,
                )
                raise ValueError("Response path does not match request path")
        else:
            raise ValueError("Response path missing")

        if (data := decoded_data[0].get(2)) is not None:

            if self.path == AtomRequestPath.CONNECTIVITY_MODE and isinstance(data, int):
                return {
                    CONNECTIVITY_MODE: AirthingsConnectivityMode.from_atom_int(
                        data
                    ).value
                }

            if self.path == AtomRequestPath.LATEST_VALUES:
                if isinstance(data, bytes):
                    # Need to use cbor2 to decode the bytes again
                    data = self._loads(data)

                if isinstance(data, dict):
                    return data

            self.logger.debug("Response data: %s", data)
            raise ValueError("Invalid response data type")
        raise ValueError("Response data missing")
