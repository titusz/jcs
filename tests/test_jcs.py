import json
from importlib.metadata import metadata

import pytest

import jcs


def test_version():
    assert jcs.__version__ == metadata("jcs")["Version"]


def test_license_metadata():
    meta = metadata("jcs")
    assert meta["License-Expression"] == "Apache-2.0"
    assert meta.get_all("License-File") == ["LICENSE", "LICENSE.PSF"]


def test_canonicalize():
    assert jcs.canonicalize({"tag": 4}) == b'{"tag":4}'


def test_canonicalize_int_key():
    with pytest.raises(TypeError, match="key 4 is not a string"):
        jcs.canonicalize({4: "tag"})


def test_canonicalize_non_string_keys_raise():
    for key in (1, 1.5, None, True, False, (1, 2)):
        for data in ({key: "a"}, {"a": 1, key: "b"}, [{"x": {key: "a"}}]):
            with pytest.raises(TypeError, match="is not a string"):
                jcs.canonicalize(data)


def test_canonicalize_nums():
    nums = {"int": 654635, "float": 26746.68731}
    assert jcs.canonicalize(nums) == b'{"float":26746.68731,"int":654635}'


def test_canonicalize_big_num():

    n = 2**53 - 1
    c = jcs.canonicalize({"tag": n})
    assert c == b'{"tag":9007199254740991}'
    assert json.loads(c)["tag"] == n


def test_canonicalize_inexact_int_raises():
    with pytest.raises(ValueError, match="Integer 9007199254740993 is not exactly"):
        jcs.canonicalize({"tag": 2**53 + 1})


def test_canonicalize_int_boundaries():
    for n in (2**53 - 1, 2**53, 2**53 + 2, -(2**53 - 1), -(2**53), -(2**53 + 2)):
        assert jcs.canonicalize(n) == str(n).encode()
    for n in (2**53 + 1, 2**53 + 3, -(2**53 + 1), -(2**53 + 3)):
        with pytest.raises(ValueError):
            jcs.canonicalize(n)


def test_canonicalize_reported_examples():
    assert jcs.canonicalize(2**60) == b"1152921504606847000"
    assert jcs.canonicalize(10**21) == b"1e+21"
    for n in (2**60 + 1, 10**21 + 1, 9007199254740993):
        with pytest.raises(ValueError):
            jcs.canonicalize({"n": n})


def test_canonicalize_inexact_int_nested_raises():
    data = {"a": [1, {"b": ("x", [2**53 + 1])}]}
    with pytest.raises(ValueError):
        jcs.canonicalize(data)


def test_canonicalize_int_beyond_double_range_raises():
    with pytest.raises(ValueError):
        jcs.canonicalize(10**400)


def test_canonicalize_bool_unchanged():
    assert jcs.canonicalize([True, False, 1, 0]) == b"[true,false,1,0]"
    assert (
        jcs.canonicalize({"t": True, "f": False, "n": None})
        == b'{"f":false,"n":null,"t":true}'
    )


def test_canonicalize_floats_unchanged():
    assert jcs.canonicalize(float(2**53 + 1)) == b"9007199254740992"
    assert jcs.canonicalize(2.0**60) == b"1152921504606847000"
    assert jcs.canonicalize(1e21) == b"1e+21"
    assert jcs.canonicalize(333333333.33333329) == b"333333333.3333333"


def test_canonicalize_parse_int_float_rounds_like_javascript():
    data = json.loads('{"n":9007199254740993}', parse_int=float)
    assert jcs.canonicalize(data) == b'{"n":9007199254740992}'


def test_canonicalize_accepted_ints_map_to_distinct_bytes():
    outputs = set()
    accepted = 0
    for n in range(2**60 - 1024, 2**60 + 1024):
        try:
            outputs.add(jcs.canonicalize(n))
        except ValueError:
            continue
        accepted += 1
    assert accepted == len(outputs) > 0


# Lone high, lone low, reversed pair, and a pair split into two code points
LONE_SURROGATES = (
    chr(0xD800),
    chr(0xDBFF),
    chr(0xDC00),
    chr(0xDFFF),
    chr(0xDE00) + chr(0xD83D),
    chr(0xD83D) + chr(0xDE00),
)


def test_canonicalize_lone_surrogates_raise():
    for s in LONE_SURROGATES:
        for data in (s, {"k": s}, {s: 1}, ["a" + s + "b"]):
            for utf8 in (True, False):
                with pytest.raises(ValueError, match="surrogates not allowed"):
                    jcs.canonicalize(data, utf8=utf8)


def test_canonicalize_supplementary_char():
    s = chr(0x1F600)
    assert jcs.canonicalize({s: s}) == b'{"\xf0\x9f\x98\x80":"\xf0\x9f\x98\x80"}'
    assert jcs.canonicalize({s: s}, utf8=False) == '{"' + s + '":"' + s + '"}'


def test_canonicalize_escaped_surrogates_from_json():
    pair = json.loads('"\\ud83d\\ude00"')
    assert jcs.canonicalize(pair, utf8=False) == '"' + chr(0x1F600) + '"'
    for text in ('"\\ud800"', '"\\udc00"', '"\\ude00\\ud83d"'):
        with pytest.raises(ValueError, match="surrogates not allowed"):
            jcs.canonicalize(json.loads(text), utf8=False)


def test_canonicalize_top_level_scalars():
    assert jcs.canonicalize(None) == b"null"
    assert jcs.canonicalize(True) == b"true"
    assert jcs.canonicalize(False) == b"false"
    assert jcs.canonicalize("tag") == b'"tag"'


def test_canonicalize_tuple():
    assert jcs.canonicalize(("A", "tuple", 7)) == b'["A","tuple",7]'


def test_canonicalize_set():
    with pytest.raises(TypeError):
        assert jcs.canonicalize({1, 2, 4}) == b""
