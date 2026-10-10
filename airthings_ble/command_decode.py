"""Decoder for the command response."""

import asyncio
import struct
from logging import Logger
from typing import Any, Optional


from airthings_ble.airthings_firmware import AirthingsChip
from airthings_ble.atom.request import AtomRequest
from airthings_ble.atom.request_path import AtomRequestPath
from airthings_ble.atom.response import AtomResponse
from airthings_ble.const import (
    BATTERY,
    COMMAND_UUID_WAVE_2,
    COMMAND_UUID_WAVE_MINI,
    COMMAND_UUID_WAVE_PLUS,
    UINT16_NO_VALUE,
)

_WAVE_PLUS_DEVICE_TYPE = 2
_WAVE_PLUS_DATE_CODED_MSP_VERSIONS = (0x0798, 0x1E98, 0x03C8, 0x04C8)


def _dotted_version(major: int, minor: int, patch: int) -> str | None:
    if major == minor == patch == 0:
        return None
    return f"{major}.{minor}.{patch}"


def _msp_version(device_type: int, raw: int) -> str | None:
    """Decode the 16-bit MSP version of a Wave Plus or Wave Radon."""
    if raw == UINT16_NO_VALUE:
        return None
    if (
        device_type == _WAVE_PLUS_DEVICE_TYPE
        and raw in _WAVE_PLUS_DATE_CODED_MSP_VERSIONS
    ):
        return f"{2010 + (raw & 0x0F)}-{(raw >> 4) & 0x0F:02d}-{raw >> 8:02d}"
    return _dotted_version(raw >> 14, (raw >> 8) & 0x3F, (raw >> 6) & 0x03)


def _semantic_version(raw: int) -> str | None:
    """Decode a 32-bit major.minor.patch.build version."""
    if raw == 0xFFFFFFFF:
        return None
    return _dotted_version(raw >> 24, (raw >> 16) & 0xFF, (raw >> 8) & 0xFF)


class CommandDecode:
    """Decoder for the command response"""

    cmd: bytes | bytearray = b"\x6d"
    format_type: str
    _header_size = 2

    def decode_data(
        self,
        logger: Logger,
        raw_data: bytearray | None,  # pylint: disable=unused-argument
    ) -> dict[str, float | str | None] | None:
        """Decoder returns dict with battery"""
        logger.debug("Command decoder not implemented")
        return {}

    def validate_data(
        self, logger: Logger, raw_data: bytearray | None
    ) -> Optional[Any]:
        """Validate data. Make sure the data is for the command."""
        if raw_data is None:
            logger.debug("Validate data: No data received")
            return None

        cmd = raw_data[0:1]
        if cmd != self.cmd:
            logger.warning(
                "Result for wrong command received, expected %s got %s",
                self.cmd.hex(),
                cmd.hex(),
            )
            return None

        payload = raw_data[self._header_size :]
        if len(payload) != struct.calcsize(self.format_type):
            logger.warning(
                "Wrong length data received (%s) versus expected (%s)",
                len(payload),
                struct.calcsize(self.format_type),
            )
            return None

        return struct.unpack(self.format_type, payload)

    def make_data_receiver(self) -> "NotificationReceiver":
        """Creates a notification receiver for the command."""
        return NotificationReceiver(
            self._header_size + struct.calcsize(self.format_type)
        )


class WaveRadonAndPlusCommandDecode(CommandDecode):
    """Decoder for the Wave Plus command response"""

    def __init__(self) -> None:
        """Initialize command decoder"""
        self.format_type = "<L2BH2B9H"

    def decode_data(
        self, logger: Logger, raw_data: bytearray | None
    ) -> dict[str, float | str | None] | None:
        """Decoder returns dict with battery and chip versions"""

        if val := self.validate_data(logger, raw_data):
            res: dict[str, float | str | None] = {}
            res[BATTERY] = val[13] / 1000.0
            res[AirthingsChip.MSP] = _msp_version(device_type=val[1], raw=val[3])
            return res

        return None


class WaveMiniCommandDecode(CommandDecode):
    """Decoder for the Wave Radon command response"""

    def __init__(self) -> None:
        """Initialize command decoder"""
        self.format_type = "<2L4B2HL4HL"

    def decode_data(
        self, logger: Logger, raw_data: bytearray | None
    ) -> dict[str, float | str | None] | None:
        """Decoder returns dict with battery and chip versions"""

        if val := self.validate_data(logger, raw_data):
            res: dict[str, float | str | None] = {}
            res[BATTERY] = val[11] / 1000.0
            res[AirthingsChip.BLE] = _semantic_version(val[1])
            res[AirthingsChip.SUB] = _semantic_version(val[8])
            return res

        return None


class SubChipVersionCommandDecode(CommandDecode):
    """Decoder for the Wave Plus and Wave Radon SUB chip version response"""

    cmd = bytes([0x72, 0x01]) + bytes(7)
    _RESPONSE_SIZE = 6
    _UNRELEASED_VERSION = (0x30, 0x30, 0x30, 0x31)

    def decode_data(
        self, logger: Logger, raw_data: bytearray | None
    ) -> dict[str, float | str | None] | None:
        """Decoder returns dict with the SUB chip version.

        The dict is empty when the device reports that it has no SUB chip
        version, and None is returned when there is no reply at all.
        """
        if raw_data is None or raw_data[0:1] != self.cmd[0:1]:
            logger.debug("Validate data: No data received")
            return None
        if len(raw_data) == self._RESPONSE_SIZE:
            _, status, major, minor, patch, build = raw_data
            version = _dotted_version(major, minor, patch)
            if (
                status == 0
                and version is not None
                and 0xFF not in (major, minor)
                and (major, minor, patch, build) != self._UNRELEASED_VERSION
            ):
                return {AirthingsChip.SUB: version}
        logger.debug("SUB chip version not supported: %s", raw_data.hex())
        return {}

    def make_data_receiver(self) -> "NotificationReceiver":
        """Creates a receiver for the first notification with the command byte."""
        return CommandNotificationReceiver(self.cmd[0:1])


class AtomCommandDecode(CommandDecode):
    """Decoder for the Atom command response"""

    def __init__(self, url: AtomRequestPath) -> None:
        """Initialize command decoder"""
        self.format_type = ""
        self.set_request(url=url)

    def set_request(self, url: AtomRequestPath = AtomRequestPath.LATEST_VALUES) -> None:
        """Update the request path for the command decoder."""
        self.request = AtomRequest(url=url)
        self.cmd = self.request.as_bytes()

    def decode_data(
        self, logger: Logger, raw_data: bytearray | None
    ) -> dict[str, float | str | None] | None:
        """Decoder returns dict with battery"""
        if raw_data is None:
            logger.debug("Validate data: No data received")
            return None
        try:
            response = AtomResponse(
                logger=logger,
                response=raw_data,
                random_bytes=self.request.random_bytes,
                path=self.request.url,
            )
            return response.parse()

        except ValueError as err:
            logger.error("Failed to decode command response: %s", err)
            return None

    def make_data_receiver(self) -> "NotificationReceiver":
        """Creates a notification receiver for the command."""
        return AtomNotificationReceiver()


class NotificationReceiver:
    """Receiver for a single notification message.

    A notification message that is larger than the MTU can get sent over multiple
    packets. This receiver knows how to reconstruct it.
    """

    message: bytearray | None

    def __init__(self, message_size: int):
        self.message = None
        self._message_size = message_size
        self._loop = asyncio.get_running_loop()
        self._future: asyncio.Future[None] = self._loop.create_future()

    def _full_message_received(self) -> bool:
        return self.message is not None and len(self.message) >= self._message_size

    def __call__(self, _: Any, data: bytearray) -> None:
        if self.message is None:
            self.message = data
        elif not self._full_message_received():
            self.message += data
        if self._full_message_received() and not self._future.done():
            self._future.set_result(None)

    @property
    def complete(self) -> bool:
        """Whether the full message has been received."""
        return self._full_message_received()

    def _on_timeout(self) -> None:
        if not self._future.done():
            self._future.set_exception(
                asyncio.TimeoutError("Timeout waiting for message")
            )

    async def wait_for_message(self, timeout: float) -> None:
        """Waits until the full message is received.

        If the full message has already been received, this method returns immediately.
        """
        if not self._full_message_received():
            timer_handle = self._loop.call_later(timeout, self._on_timeout)
            try:
                await self._future
            finally:
                timer_handle.cancel()


class CommandNotificationReceiver(NotificationReceiver):
    """Receiver for the first notification that starts with the command byte.

    Notifications for other commands, such as a late reply to an earlier
    command, are ignored.
    """

    def __init__(self, command: bytes) -> None:
        super().__init__(message_size=1)
        self._command = command

    def __call__(self, sender: Any, data: bytearray) -> None:
        if data[0:1] == self._command:
            super().__call__(sender, data)


class AtomNotificationReceiver(NotificationReceiver):
    """Receiver that reassembles an Atom response from its fragments.

    Every notification starts with a three byte fragment header. In the control
    byte, the low nibble is the fragmentation version, bit 4 marks the first
    fragment and the top three bits identify the response. The two little-endian
    bytes after it hold the number of fragments in the first fragment, and the
    fragment's position, counting from one, in the others.
    """

    _FRAGMENT_HEADER_SIZE = 3

    def __init__(self) -> None:
        super().__init__(message_size=0)
        self._fragments: dict[int, dict[int, bytes]] = {}
        self._fragment_count = 0
        self._object_id: int | None = None

    def _full_message_received(self) -> bool:
        return self.message is not None

    def __call__(self, _: Any, data: bytearray) -> None:
        if self.message is not None or len(data) < self._FRAGMENT_HEADER_SIZE:
            return
        control = data[0]
        if control & 0x0F:
            return
        object_id = control & 0xE0
        if self._object_id is not None and object_id != self._object_id:
            return
        number = int.from_bytes(data[1:3], "little")
        fragments = self._fragments.setdefault(object_id, {})
        payload = bytes(data[self._FRAGMENT_HEADER_SIZE :])
        if control & 0x10:
            self._object_id = object_id
            self._fragment_count = number
            fragments[1] = payload
        elif number > 1:
            fragments[number] = payload
        if self._object_id is None:
            return
        fragments = self._fragments[self._object_id]
        positions = range(1, self._fragment_count + 1)
        if positions and all(position in fragments for position in positions):
            self.message = bytearray(
                b"".join(fragments[position] for position in positions)
            )
            if not self._future.done():
                self._future.set_result(None)


COMMAND_DECODERS: dict[str, CommandDecode] = {
    str(COMMAND_UUID_WAVE_2): WaveRadonAndPlusCommandDecode(),
    str(COMMAND_UUID_WAVE_PLUS): WaveRadonAndPlusCommandDecode(),
    str(COMMAND_UUID_WAVE_MINI): WaveMiniCommandDecode(),
}
