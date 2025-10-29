"""Decoder for the command response."""

import asyncio
import struct
from logging import Logger
from typing import Any, Optional

from airthings_ble.atom.request import AtomRequest
from airthings_ble.atom.request_path import AtomRequestPath
from airthings_ble.atom.response import AtomResponse
from airthings_ble.const import (
    BATTERY,
    COMMAND_UUID_WAVE_2,
    COMMAND_UUID_WAVE_MINI,
    COMMAND_UUID_WAVE_PLUS,
)


class CommandDecode:
    """Decoder for the command response"""

    cmd: bytes = b"\x6d"
    format_type: str

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

        if len(raw_data[2:]) != struct.calcsize(self.format_type):
            logger.warning(
                "Wrong length data received (%s) versus expected (%s)",
                len(raw_data[2:]),
                struct.calcsize(self.format_type),
            )
            return None

        return struct.unpack(self.format_type, raw_data[2:])

    def make_data_receiver(self) -> "NotificationReceiver":
        """Creates a notification receiver for the command."""
        return NotificationReceiver(struct.calcsize(self.format_type))


class WaveRadonAndPlusCommandDecode(CommandDecode):
    """Decoder for the Wave Plus command response"""

    def __init__(self) -> None:
        """Initialize command decoder"""
        self.format_type = "<L2BH2B9H"

    def decode_data(
        self, logger: Logger, raw_data: bytearray | None
    ) -> dict[str, float | str | None] | None:
        """Decoder returns dict with battery"""

        if val := self.validate_data(logger, raw_data):
            res = {}
            res[BATTERY] = val[13] / 1000.0
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
        """Decoder returns dict with battery"""

        if val := self.validate_data(logger, raw_data):
            res = {}
            res[BATTERY] = val[11] / 1000.0

            return res

        return None


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
        if self._full_message_received():
            self._future.set_result(None)

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


COMMAND_DECODERS: dict[str, CommandDecode] = {
    str(COMMAND_UUID_WAVE_2): WaveRadonAndPlusCommandDecode(),
    str(COMMAND_UUID_WAVE_PLUS): WaveRadonAndPlusCommandDecode(),
    str(COMMAND_UUID_WAVE_MINI): WaveMiniCommandDecode(),
}
