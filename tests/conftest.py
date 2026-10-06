import logging

import pytest


@pytest.fixture(autouse=True)
def fail_on_command_timeout(
    request: pytest.FixtureRequest, caplog: pytest.LogCaptureFixture
):
    caplog.set_level(logging.DEBUG)
    yield
    if request.node.get_closest_marker("command_timeout") is None:
        assert not [
            record
            for record in caplog.get_records("call")
            if "Timeout getting command data" in record.getMessage()
        ]
