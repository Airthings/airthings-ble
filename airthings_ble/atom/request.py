import os
from airthings_ble.atom.request_path import AtomRequestPath


class AtomRequest:
    """Request for Airthings BLE Atom API"""

    url: AtomRequestPath
    random_bytes: bytes

    def __init__(
        self, url: AtomRequestPath, random_bytes: bytes | None = None
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
