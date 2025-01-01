"""Request for data from a Wave Enhance"""

import enum
from logging import Logger
import os
import cbor2


class WaveEnhanceRequestPath(enum.Enum):
    """URLs for the Wave Enhance"""

    LATEST_VALUES = "29999/0/31012"

    def as_bytes(self) -> bytes:
        """Get URL as bytes"""
        if not isinstance(self.value, str):
            raise ValueError(
                "WaveEnhanceRequestPath - self.value must be a string to encode: %s, type: %s",
                self.value,
                type(self.value),
            )
        return bytes(self.value, "utf-8")


class WaveEnhanceRequest:
    """Request for data from a Wave Enhance"""

    url: WaveEnhanceRequestPath
    random_bytes: bytes

    def __init__(
        self, url: WaveEnhanceRequestPath, random_bytes: bytes | None = None
    ) -> None:
        self.url = url
        if random_bytes is not None:
            self.random_bytes = random_bytes
        else:
            self.random_bytes = os.urandom(2)

    def as_bytes(self) -> bytes:
        """Get request as bytes"""
        bytes = bytearray()
        bytes.extend(bytes.fromhex("0301"))
        bytes.extend(self.random_bytes)
        bytes.extend(bytes.fromhex("81A1006D"))
        bytes.extend(self.url.as_bytes())
        return bytes


class WaveEnhanceResponse:
    """Response from a Wave Enhance"""

    _header = bytearray.fromhex("1001000345")
    response: bytes
    random_bytes: bytes
    path: WaveEnhanceRequestPath

    def __init__(
        self,
        logger: Logger,
        response: bytes | None,
        random_bytes: bytes,
        path: WaveEnhanceRequestPath,
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
                "Invalid response type, expected 1, but got %s", self.response[7]
            )
            raise ValueError("Invalid response type")

        if self.response[8] != 0xA2:
            self.logger.debug(
                "Invalid response array length, expected 2, but got %s",
                self.response[8],
            )
            raise ValueError("Invalid response array length")

        if self.response[9] != 0x00:
            self.logger.debug(
                "Invalid response data type, expected 00, but got %s", self.response[9]
            )
            raise ValueError("Invalid response element")

        path_length = self.response[10] - 0x60
        if path_length != len(self.path.as_bytes()):
            self.logger.debug(
                "Invalid path length, expected %d, but got %d",
                len(self.path.as_bytes()),
                path_length,
            )
            raise ValueError("Invalid response path length")

        if self.response[11 : 11 + path_length] != self.path.as_bytes():
            self.logger.debug(
                "Invalid response path, expected %s, but got %s",
                self.path.as_bytes(),
                self.response[11 : 11 + path_length],
            )
            raise ValueError("Invalid response path")

        try:
            self.logger.debug("Response: %s", self.response.hex())

            data_bytes = self.response[27:]

            decoded_data = cbor2.loads(data_bytes)
            self.logger.debug("Decoded data: %s", decoded_data)

            if not isinstance(decoded_data, dict):
                self.logger.error(
                    "Parsed data is not a dictionary, but a %s", type(decoded_data)
                )
                raise ValueError("Invalid response data type")
            return decoded_data
        except ValueError as e:
            self.logger.error(f"Failed to parse response: {e}")
            return None
