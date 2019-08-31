from shifty import __version__
from shifty.app import ops


def test_version():
    assert __version__ == "0.1.0"


def test_ops():
    ops()
