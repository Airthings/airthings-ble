"""Request for data from a Wave Enhance"""

import enum
import logging
import os

import cbor2
import traceback


_LOGGER = logging.getLogger(__name__)


class WaveEnhanceRequestPath(enum.Enum):
    """URLs for the Wave Enhance"""

    LATEST_VALUES = "29999/0/31012"

    def as_bytes(self) -> bytes:
        """Get URL as bytes"""

        _LOGGER.warning("WaveEnhanceRequestPath - as_bytes")
        _LOGGER.warning("WaveEnhanceRequestPath - self.value: %s", self.value)
        _LOGGER.warning("WaveEnhanceRequestPath - type(self.value): %s", type(self.value))

        if not isinstance(self.value, str):
            raise ValueError(
                "WaveEnhanceRequestPath - self.value must be a string to encode: %s, type: %s",
                self.value,
                type(self.value)
            )

        try:
            random_stuff = bytes(self.value, "utf-8")
            _LOGGER.warning("WaveEnhanceRequestPath - Random stuff: %s", random_stuff)
        except Exception as e:
            _LOGGER.error(f"WaveEnhanceRequestPath - Failed to encode: {e}")
            raise e

        return bytes(self.value, "utf-8")


class WaveEnhanceRequest:
    """Request for data from a Wave Enhance"""

    url: WaveEnhanceRequestPath
    random_bytes: bytes

    def __init__(self, url: WaveEnhanceRequestPath):
        self.url = url
        self.random_bytes = os.urandom(4)

    def as_bytes(self) -> bytes:
        """Get request as bytes"""

        # TODO: Add random bytes, dynamic URL etc
        return bytes.fromhex("0301FAA981A1006D32393939392F302F3331303132")


class WaveEnhanceResponse:
    """Response from a Wave Enhance"""

    # Expected header
    # 1001000345, but got 1001000384
    _header = bytearray.fromhex("1001000345")

    _checksum = bytearray.fromhex("FAA9")

    response: bytes
    random_bytes: bytes
    path: WaveEnhanceRequestPath

    def __init__(
            self,
            response: bytes | None,
            random_bytes: bytes,
            path: WaveEnhanceRequestPath
            ) -> None:
        _LOGGER.warning("WaveEnhanceResponse - Response: %s", response)
        if response is None:
            raise ValueError("Response cannot be None")
        self.response = response

        _LOGGER.warning("WaveEnhanceResponse - Random bytes: %s", random_bytes)
        self.random_bytes = random_bytes

        _LOGGER.warning("WaveEnhanceResponse - Path: %s", path)
        self.path = path.as_bytes()

        _LOGGER.warning("WaveEnhanceResponse - done")

    def parse(self) -> dict[str, float | str | None] | None:
        if self.response[0:5] != self._header:
            _LOGGER.error(
                "Invalid response header, expected %s, but got %s",
                self._header.hex(),
                self.response[0:5].hex()
            )
            # raise ValueError("Invalid response header")

        if self.response[5:7] != self._checksum:
            _LOGGER.error(
                "Invalid response checksum, expected %s, but got %s",
                self._checksum,
                self.response[5:7]
            )
            raise ValueError("Invalid response checksum")

        if self.response[7] != 0x81:
            _LOGGER.error(
                "Invalid response type, expected 1, but got %s",
                self.response[7]
            )
            raise ValueError("Invalid response type")

        if self.response[8] != 0xA2:
            _LOGGER.error(
                "Invalid response array length, expected 2, but got %s",
                self.response[8]
            )
            raise ValueError("Invalid response array length")

        if self.response[9] != 0x00:
            _LOGGER.error(
                "Invalid response data type, expected 00, but got %s",
                self.response[9]
            )
            raise ValueError("Invalid response element")

        path_length = self.response[10] - 0x60
        if path_length != len(self.path):
            _LOGGER.error(
                "Invalid path length, expected %d, but got %d",
                len(self.path),
                path_length
            )
            raise ValueError("Invalid response path length")

        if self.response[11:11 + path_length] != self.path:
            _LOGGER.error(
                "Invalid response path, expected %s, but got %s",
                self.path,
                self.response[11:11 + path_length]
            )
            raise ValueError("Invalid response path")

        try:
            _LOGGER.warning("Response: %s", self.response.hex())

            data_bytes = self.response[27:]
            _LOGGER.warning("Data bytes: %s", data_bytes)

            decoded_data = cbor2.loads(data_bytes)
            _LOGGER.warning("Decoded data: %s", decoded_data)

            # TODO: Validate data type

            _LOGGER.warning("Parsed data is type: %s", type(decoded_data))

            return decoded_data
        except ValueError as e:
            _LOGGER.error(f"Failed to parse response: {e}")
            return None
