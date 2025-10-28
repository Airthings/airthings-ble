import asyncio
import struct
from enum import Enum
from logging import Logger
from typing import Any, Optional

from airthings_ble.atom.request import AtomRequest
from airthings_ble.atom.request_path import AtomRequestPath
from airthings_ble.atom.response import AtomResponse
from airthings_ble.connectivity_type import AirthingsConnectivityMode
from airthings_ble.const import (
    COMMAND_UUID_WAVE_2,
    COMMAND_UUID_WAVE_MINI,
    COMMAND_UUID_WAVE_PLUS,
)


class Commands(bytes, Enum):
    """Commands for Airthings BLE devices"""
    BATTERY = b"\x6d"
    CONNECTIVITY_WAVE_MINI = b"\x71\x80 \x0a\x00\x00\x00\x00\x00\x00\x00"
    CONNECTIVITY_WAVE_PLUS_AND_RADON = b"\x71\x53\x0a\x00\x00\x00\x00\x00\x00\x00"

    def as_request_bytes(self) -> bytes:
        """Returns the command as bytes for request"""
        if self == Commands.CONNECTIVITY_WAVE_PLUS_AND_RADON:
            return self.value
        return self.value

    def verify_response(self, response: bytearray) -> bool:
        """Verifies if the response matches the command."""
        if self == Commands.CONNECTIVITY_WAVE_PLUS_AND_RADON:
            if response[0:1] == b"\x71" and response[2:5] == b"\x53\x0a\x00":
                return True
            return False
            
        # TODO: Implement Wave Mini

        return response[0:1] == self.value


class CommandDecode:
    """Decoder for the command response"""

    cmd: Commands = Commands.BATTERY
    format_type: str

    @property
    def only_on_first_attempt(self) -> bool:
        if self.cmd == Commands.BATTERY:
            return True
        return False

    def decode_data(
        self,
        logger: Logger,
        raw_data: bytearray | None,  # pylint: disable=unused-argument
    ) -> dict[str, float | str | None] | None:
        """Decoder returns dict with battery"""
        logger.debug("Command decoder not implemented")
        return {}

    def validate_data(
        self, logger: Logger, raw_data: bytearray
    ) -> Optional[Any]:
        """Validate data. Make sure the data is for the command."""
        cmd = raw_data[0:1]
        if cmd != self.cmd[0:1]:
            logger.warning(
                "Result for wrong command received, expected %s got %s",
                self.cmd.hex(),
                cmd.hex(),
            )
            return None

        if len(raw_data[2:]) != struct.calcsize(self.format_type):
            logger.warning(
                "Wrong length data received (%s) versus expected (%s) for command %s",
                len(raw_data[2:]),
                struct.calcsize(self.format_type),
                self.cmd.hex(),
            )
            return None

        return struct.unpack(self.format_type, raw_data[2:])

    def make_data_receiver(self) -> "NotificationReceiver":
        """Creates a notification receiver for the command."""
        return NotificationReceiver(struct.calcsize(self.format_type))


class WaveRadonAndPlusCommandDecode(CommandDecode):
    """Decoder for the Wave Plus command response"""

    def __init__(self, command: Commands) -> None:
        """Initialize command decoder"""
        if command == Commands.BATTERY:
            self.format_type = "<L2BH2B9H"
        else:
            # TODO: Update me to correct format
            self.format_type = "<9b"
        self.cmd = command
        self.command = command

    def decode_data(
        self, logger: Logger, raw_data: bytearray | None
    ) -> dict[str, float | str | None] | None:
        """Decoder returns dict with battery"""

        if not raw_data:
            logger.warning("No data received for command decoding")
            return None

        val = self.validate_data(logger, raw_data)
        if val is None:
            logger.warning(
                "Validation of data failed for command decoding"
            )
            return None

        res = {}

        if not self.cmd.verify_response(raw_data):
            logger.warning(
                "Response verification failed for command decoding"
            )
            return None

        if self.cmd == Commands.BATTERY:
            res["battery"] = val[13] / 1000.0
            return res
        elif self.cmd == Commands.CONNECTIVITY_WAVE_PLUS_AND_RADON:
            connectivity_mode = AirthingsConnectivityMode.from_wave_int(val[5])
            res["connectivity_mode"] = connectivity_mode.value
            return res
        logger.warning(
            "Unknown command response received."
        )
        return None


class WaveMiniCommandDecode(CommandDecode):
    """Decoder for the Wave Radon command response"""

    def __init__(self, command: Commands) -> None:
        """Initialize command decoder"""
        if command == Commands.BATTERY:
            self.format_type = "<2L4B2HL4HL"
        else:
            # Need to fetch 7..<10 as Int32
            # All bytes (8 bit)
            self.format_type = ""
        self.cmd = command

    def decode_data(
        self, logger: Logger, raw_data: bytearray | None
    ) -> dict[str, float | str | None] | None:
        """Decoder returns dict with battery"""
        if not raw_data:
            logger.warning("No data received for command decoding")
            return None

        val = self.validate_data(logger, raw_data)
        if val is None:
            return None

        res = {}
        cmd = raw_data[0:1]
        if cmd == Commands.BATTERY.value:
            res["battery"] = val[11] / 1000.0
        elif cmd == Commands.CONNECTIVITY_WAVE_MINI.value:
            # TODO: Change me to correct value
            res["connectivity_mode"] = val[11]
        else:
            logger.warning(
                "Unknown command response received: %s", cmd.hex()
            )
            return None

        return res


class AtomCommandDecode(CommandDecode):
    """Decoder for the Atom command response"""

    def __init__(self, url: AtomRequestPath) -> None:
        """Initialize command decoder"""
        self.format_type = ""
        self.set_request(url=url)

    def set_request(self, url: AtomRequestPath = AtomRequestPath.LATEST_VALUES) -> None:
        """Update the request path for the command decoder."""
        self.request = AtomRequest(url=url)
        # self.cmd = self.request.as_bytes()

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
    str(COMMAND_UUID_WAVE_2): WaveRadonAndPlusCommandDecode(Commands.BATTERY),
    str(COMMAND_UUID_WAVE_2): WaveRadonAndPlusCommandDecode(
        Commands.CONNECTIVITY_WAVE_PLUS_AND_RADON
    ),
    str(COMMAND_UUID_WAVE_PLUS): WaveRadonAndPlusCommandDecode(Commands.BATTERY),
    str(COMMAND_UUID_WAVE_PLUS): WaveRadonAndPlusCommandDecode(
        Commands.CONNECTIVITY_WAVE_PLUS_AND_RADON
    ),
    str(COMMAND_UUID_WAVE_MINI): WaveMiniCommandDecode(Commands.BATTERY),
    str(COMMAND_UUID_WAVE_MINI): WaveMiniCommandDecode(Commands.CONNECTIVITY_WAVE_MINI),
}
