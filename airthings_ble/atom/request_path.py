from enum import Enum


class WaveEnhanceRequestPath(Enum):
    """Request paths for Airthings BLE Atom API"""

    LATEST_VALUES = "29999/0/31012"

    def as_bytes(self) -> bytes:
        """Get URL as bytes"""
        if not isinstance(self.value, str):
            raise ValueError(
                "Request path value must be a string: %s, type: %s",
                self.value,
                type(self.value),
            )
        return bytes(self.value, "utf-8")
