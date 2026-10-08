from logging import Logger

import cbor2
from airthings_ble.atom.request import AtomRequestPath
from airthings_ble.connectivity_mode import AirthingsConnectivityMode
from airthings_ble.const import ATOM_RESPONSE_HEADER, CONNECTIVITY_MODE


class AtomResponse:
    """Response for Airthings BLE Atom API"""

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
        if self.response[0:2] != ATOM_RESPONSE_HEADER:
            self.logger.error(
                "Invalid response header, expected %s, but got %s",
                ATOM_RESPONSE_HEADER.hex(),
                self.response[0:2].hex(),
            )
            raise ValueError("Invalid response header")

        if self.response[2:4] != self.random_bytes:
            self.logger.debug(
                "Invalid response checksum, expected %s, but got %s",
                self.random_bytes.hex(),
                self.response[2:4].hex(),
            )
            raise ValueError("Invalid response checksum")

        if len(self.response) < 6:
            raise ValueError("Response too short")

        if self.response[4] != 0x81:
            self.logger.debug(
                "Invalid response type, expected 81, but got %s", self.response[4]
            )
            raise ValueError("Invalid response type")

        if self.response[5] != 0xA2:
            self.logger.debug(
                "Invalid response array length, expected 2, but got %s",
                self.response[5],
            )
            raise ValueError("Invalid response array length")

        data_bytes = self.response[4:]
        decoded_data = self._loads(data_bytes)

        if not isinstance(decoded_data, list):
            self.logger.debug("Parsed data is not a list, but a %s", type(decoded_data))
            raise ValueError("Invalid response data type")

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

            if (
                self.path == AtomRequestPath.CONNECTIVITY_MODE
                and isinstance(data, int)
                and not isinstance(data, bool)
            ):
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
