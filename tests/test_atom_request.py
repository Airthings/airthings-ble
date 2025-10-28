from airthings_ble.atom.request import AtomRequest
from airthings_ble.atom.request_path import AtomRequestPath
from pytest import mark


@mark.parametrize(
    "random_bytes",
    [
        None,
        bytes.fromhex("E473"),
        bytes.fromhex("A1B2"),
    ],
)
def test_atom_request_latest_values(random_bytes: bytes | None) -> None:
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
    assert request_bytes[4:7] == bytes.fromhex("81A100")
    assert request_bytes[8:] == request.url.as_bytes()


def test_atom_request_connectivity_mode() -> None:
    """Test the Wave Enhance request."""
    request = AtomRequest(url=AtomRequestPath.CONNECTIVITY_MODE)
    assert request.url == AtomRequestPath.CONNECTIVITY_MODE

    request_bytes = request.as_bytes()

    assert request_bytes[0:2] == bytes.fromhex("0301")
    assert request_bytes[4:7] == bytes.fromhex("81A100")
    assert request_bytes[8:] == request.url.as_bytes()


def test_invalid_random_bytes() -> None:
    """Test invalid random bytes."""
    try:
        AtomRequest(
            url=AtomRequestPath.LATEST_VALUES,
            random_bytes=bytes.fromhex("A1B2C3"),
        )
    except ValueError as exc:
        assert str(exc) == "Random bytes must be exactly 2 bytes long"
