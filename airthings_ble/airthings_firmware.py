class AirthingsFirmware:
    """Firmware information for the Airthings device."""

    need_fw_upgrade = False
    current_firmware: str | None = None
    needed_firmware: str | None = None

    def __init__(
        self,
        need_fw_upgrade: bool = False,
        current_firmware: str | None = None,
        needed_firmware: str | None = None,
    ) -> None:
        self.need_fw_upgrade = need_fw_upgrade
        self.current_firmware = current_firmware
        self.needed_firmware = needed_firmware
