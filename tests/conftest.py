import logging

import pytest

from fakes import CALLBACK_ERRORS


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


@pytest.fixture(autouse=True)
def fail_on_notification_callback_error():
    CALLBACK_ERRORS.clear()
    yield
    assert not CALLBACK_ERRORS
