from logging import Logger

import cbor2
from airthings_ble.atom.request import AtomRequestPath


class AtomResponse:
    """Response for Airthings BLE Atom API"""

    _header = bytearray.fromhex("1001000345")
    response: bytes
    random_bytes: bytes
    path: AtomRequestPath

    def __init__(
        self,
        logger: Logger,
        response: bytes | None,
        random_bytes: bytes,
        path: AtomRequestPath,
    ) -> None:
        self.logger = logger
        if response is None:
            raise ValueError("Response cannot be None")
        self.response = response
        self.random_bytes = random_bytes
        self.path = path

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

        try:
            self.logger.debug("Response: %s", self.response.hex())

            data_bytes = self.response[7:]
            decoded_data = cbor2.loads(data_bytes)
            self.logger.debug("Decoded data: %s", decoded_data)
        except ValueError as e:
            self.logger.error(f"Failed to parse response: {e}")
            return None

        if not isinstance(decoded_data, list):
            self.logger.error(
                "Parsed data is not a list, but a %s", type(decoded_data)
            )
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

        if data := decoded_data[0].get(2):
            expected_type = self.path.expected_response_type()
            if isinstance(data, expected_type):
                self.logger.error("Parsed data: %s", data)
                return data
            self.logger.error(
                "Response data: %s", data
            )
            raise ValueError(
                (
                    "Invalid response data type, expected "
                    f"{expected_type} but got {type(data)}"
                )
            )
        raise ValueError("Response data missing")
