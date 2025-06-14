from pytest import mark
from airthings_ble.atom.request import AtomRequest
from airthings_ble.atom.request_path import AtomRequestPath


@mark.parametrize(
    "random_bytes",
    [
        None,
        bytes.fromhex("E473"),
    ],
)
def test_atom_request(random_bytes: bytes | None):
    """Test the Wave Enhance request."""
    request = AtomRequest(url=AtomRequestPath.LATEST_VALUES, random_bytes=random_bytes)
    assert request.url == AtomRequestPath.LATEST_VALUES
    assert len(request.random_bytes) == 2
    if random_bytes is not None:
        assert request.random_bytes == random_bytes
    else:
        random_bytes = request.random_bytes

    request_bytes = request.as_bytes()

    assert request_bytes[0:2] == bytes.fromhex("0301")
    assert request_bytes[2:4] == random_bytes
    assert request_bytes[4:8] == bytes.fromhex("81A1006D")
    assert request_bytes[8:] == request.url.as_bytes()
