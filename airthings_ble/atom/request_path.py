from enum import Enum
import cbor2


class AtomRequestPath(Enum):
    """Request paths for Airthings BLE Atom API"""

    LATEST_VALUES = "29999/0/31012"

    def as_cbor(self) -> bytes:
        """Get URL as bytes"""
        return cbor2.dumps([{0: self.value}])

    def as_bytes(self) -> bytes:
        """Get URL as bytes"""
        return bytes(self.value, "utf-8")
