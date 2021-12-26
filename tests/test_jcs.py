import jcs


def test_version():
    assert jcs.__version__ == "0.1.0"


def test_canonicalize():
    assert jcs.canonicalize({"tag": 4}) == b'{"tag":4}'
