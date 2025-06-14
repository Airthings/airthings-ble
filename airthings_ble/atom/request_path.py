from enum import StrEnum
import cbor2


class AtomRequestPath(StrEnum):
    """Request paths for Airthings BLE Atom API"""

    LATEST_VALUES = "29999/0/31012"

    def as_cbor(self) -> bytes:
        """Get URL as bytes"""
        return cbor2.dumps(self.value)

    def as_bytes(self) -> bytes:
        """Get URL as bytes"""
        return bytes(self.value, "utf-8")
