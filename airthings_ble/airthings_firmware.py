class AirthingsFirmware:  # pylint: disable=too-few-public-methods
    """Firmware information for the Airthings device."""

    need_fw_upgrade = False
    current_firmware = ""
    needed_firmware = ""

    def __init__(
        self,
        need_fw_upgrade: bool = False,
        current_firmware: str = "",
        needed_firmware: str = "",
    ) -> None:
        self.need_fw_upgrade = need_fw_upgrade
        self.current_firmware = current_firmware
        self.needed_firmware = needed_firmware
