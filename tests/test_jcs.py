import pytest
import jcs
import json


def test_version():
    assert jcs.__version__ == "0.1.0"


def test_canonicalize():
    assert jcs.canonicalize({"tag": 4}) == b'{"tag":4}'


def test_canonicalize_int_key():
    with pytest.raises(AttributeError):
        assert jcs.canonicalize({4: "tag"})


def test_canonicalize_big_num():

    n = 2 ** 53 - 1
    c = jcs.canonicalize({"tag": n})
    assert c == b'{"tag":9007199254740991}'
    assert json.loads(c)["tag"] == n

    # overflow
    n = 2 ** 53 + 1
    c = jcs.canonicalize({"tag": n})
    assert c == b'{"tag":9007199254740992}'
    with pytest.raises(AssertionError):
        assert json.loads(c)["tag"] == n
