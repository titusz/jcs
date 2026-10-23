"""Unit tests for jcs.canonicalize: numbers, dict keys, strings, and supported types."""

import json
from importlib.metadata import metadata

import pytest

import jcs


def test_version():
    """The package version matches the installed distribution metadata."""
    assert jcs.__version__ == metadata("jcs")["Version"]


def test_license_metadata():
    """The distribution declares Apache-2.0 and ships both license files."""
    meta = metadata("jcs")
    assert meta["License-Expression"] == "Apache-2.0"
    assert meta.get_all("License-File") == ["LICENSE", "LICENSE.PSF"]


def test_canonicalize():
    """A simple dict serializes to compact UTF-8 bytes."""
    assert jcs.canonicalize({"tag": 4}) == b'{"tag":4}'


def test_canonicalize_int_key():
    """An integer dict key raises TypeError naming its type."""
    with pytest.raises(TypeError, match="key of type int is not a string"):
        jcs.canonicalize({4: "tag"})


def test_canonicalize_non_string_keys_raise():
    """Non-string keys raise TypeError at any depth, alone or next to string keys."""
    for key in (1, 1.5, None, True, False, (1, 2)):
        for data in ({key: "a"}, {"a": 1, key: "b"}, [{"x": {key: "a"}}]):
            with pytest.raises(TypeError, match="is not a string"):
                jcs.canonicalize(data)


def test_canonicalize_huge_int_key_raises_type_error():
    """The key error does not convert the key to str, which fails beyond 4300 digits."""
    with pytest.raises(TypeError, match="key of type int is not a string"):
        jcs.canonicalize({10**5000: 1})


def test_canonicalize_nums():
    """Integers and floats serialize in ES6 number format."""
    nums = {"int": 654635, "float": 26746.68731}
    assert jcs.canonicalize(nums) == b'{"float":26746.68731,"int":654635}'


def test_canonicalize_big_num():
    """The largest safe integer serializes as is and reads back unchanged."""
    n = 2**53 - 1
    c = jcs.canonicalize({"tag": n})
    assert c == b'{"tag":9007199254740991}'
    assert json.loads(c)["tag"] == n


def test_canonicalize_inexact_int_raises():
    """An integer that is not a double raises ValueError naming its nearest double."""
    with pytest.raises(
        ValueError,
        match="Integer 9007199254740993 is not exactly.*double 9007199254740992 serializes",
    ):
        jcs.canonicalize({"tag": 2**53 + 1})


def test_canonicalize_int_boundaries():
    """Integers around 2**53 are accepted if and only if they are exact doubles."""
    for n in (2**53 - 1, 2**53, 2**53 + 2, -(2**53 - 1), -(2**53), -(2**53 + 2)):
        assert jcs.canonicalize(n) == str(n).encode()
    for n in (2**53 + 1, 2**53 + 3, -(2**53 + 1), -(2**53 + 3)):
        with pytest.raises(ValueError):
            jcs.canonicalize(n)


def test_canonicalize_reported_examples():
    """Examples from issue #1 raise, including 2**60 and its canonical form."""
    assert jcs.canonicalize(10**21) == b"1e+21"
    for n in (2**60, 1152921504606847000, 2**60 + 1, 10**21 + 1, 9007199254740993):
        with pytest.raises(ValueError):
            jcs.canonicalize({"n": n})


def test_canonicalize_exact_doubles_reading_back_differently_raise():
    """Exact doubles below 1e21 raise if their shortest form is a different integer."""
    for n, es6 in ((2**60, "1152921504606847000"), (-(2**63), "-9223372036854776000")):
        with pytest.raises(
            ValueError, match="double " + str(n) + " serializes as " + es6
        ):
            jcs.canonicalize(n)


def test_canonicalize_shortest_forms_of_doubles_raise():
    """Integers written like a double's shortest form raise unless they equal that double."""
    texts = (
        "295147905179352830000",  # RFC 8785, Appendix B: the double 2**68
        "1152921504606847000",
        "9223372036854776000",
        "-9223372036854776000",
        "1234567890123456800",
    )
    for text in texts:
        with pytest.raises(ValueError, match="nearest IEEE 754 double"):
            jcs.canonicalize(int(text))


def test_canonicalize_exact_shortest_forms_accepted():
    """Integers above 2**53 that are exact doubles and their own shortest form are accepted."""
    for n in (2**54, 10**17, 1729700000000000000, -(10**20)):
        assert jcs.canonicalize(n) == str(n).encode()


def test_canonicalize_ints_from_1e21():
    """From 1e21 on, output has an exponent and reads back as float, so only exact doubles pass."""
    assert jcs.canonicalize(10**21) == b"1e+21"
    assert jcs.canonicalize(2**70) == b"1.1805916207174113e+21"
    for n in (10**23, 10**300, 2**70 + 1):
        with pytest.raises(ValueError, match="not exactly representable"):
            jcs.canonicalize(n)


def test_canonicalize_output_reads_back():
    """Canonical integers read with json.loads canonicalize to the same bytes again."""
    for n in (2**53 + 2, 2**54, 10**17, -(10**20), 10**21, 2**70):
        canonical = jcs.canonicalize(n)
        assert json.loads(canonical) == n
        assert jcs.canonicalize(json.loads(canonical)) == canonical


def test_canonicalize_double_producer_text_needs_parse_int_float():
    """Canonical text from double-based producers like JavaScript verifies with parse_int=float.

    Plain json.loads reads 1152921504606847000 as an integer that is not a double, which raises.
    Reading it as float gives the double the producer serialized, and the same bytes again.
    """
    for text in (
        b"295147905179352830000",
        b"1152921504606847000",
        b"9223372036854776000",
    ):
        with pytest.raises(ValueError):
            jcs.canonicalize(json.loads(text))
        assert jcs.canonicalize(json.loads(text, parse_int=float)) == text


def test_canonicalize_inexact_int_nested_raises():
    """An inexact integer nested in dicts, lists, and tuples raises ValueError."""
    data = {"a": [1, {"b": ("x", [2**53 + 1])}]}
    with pytest.raises(ValueError):
        jcs.canonicalize(data)


def test_canonicalize_int_beyond_double_range_raises():
    """Integers beyond the double range raise with their bit length, not their digits."""
    for n, bits in ((10**400, 1329), (-(10**5000), 16610)):
        with pytest.raises(
            ValueError, match="Integer with " + str(bits) + " bits is not exactly"
        ):
            jcs.canonicalize(n)


def test_canonicalize_bool_unchanged():
    """Booleans serialize as true and false, not as integers."""
    assert jcs.canonicalize([True, False, 1, 0]) == b"[true,false,1,0]"
    assert (
        jcs.canonicalize({"t": True, "f": False, "n": None})
        == b'{"f":false,"n":null,"t":true}'
    )


def test_canonicalize_floats_unchanged():
    """Floats serialize in their shortest form without any read-back check."""
    assert jcs.canonicalize(float(2**53 + 1)) == b"9007199254740992"
    assert jcs.canonicalize(2.0**60) == b"1152921504606847000"
    assert jcs.canonicalize(1e21) == b"1e+21"
    assert jcs.canonicalize(333333333.33333329) == b"333333333.3333333"


def test_canonicalize_parse_int_float_rounds_like_javascript():
    """Parsing integers as floats rounds them to the nearest double like JavaScript does."""
    data = json.loads('{"n":9007199254740993}', parse_int=float)
    assert jcs.canonicalize(data) == b'{"n":9007199254740992}'


def test_canonicalize_accepted_numbers_map_to_distinct_bytes():
    """Accepted integers and floats share canonical bytes only if they are equal in value.

    Around 2**60, the integer 1152921504606847000 must not share bytes with the float 2.0**60.
    """
    values = {}
    accepted_ints = 0
    for base in (2**53, 10**17, 2**60):
        for n in range(base - 1024, base + 1024):
            for value in (n, float(n)):
                try:
                    canonical = jcs.canonicalize(value)
                except ValueError:
                    continue
                accepted_ints += isinstance(value, int)
                assert values.setdefault(canonical, value) == value
    assert accepted_ints > 0


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
    """Lone surrogates in values and keys raise ValueError in both output modes."""
    for s in LONE_SURROGATES:
        for data in (s, {"k": s}, {s: 1}, ["a" + s + "b"]):
            for utf8 in (True, False):
                with pytest.raises(ValueError, match="surrogates not allowed"):
                    jcs.canonicalize(data, utf8=utf8)


def test_canonicalize_supplementary_char():
    """Characters beyond the BMP serialize as UTF-8 bytes or as the character itself."""
    s = chr(0x1F600)
    assert jcs.canonicalize({s: s}) == b'{"\xf0\x9f\x98\x80":"\xf0\x9f\x98\x80"}'
    assert jcs.canonicalize({s: s}, utf8=False) == '{"' + s + '":"' + s + '"}'


def test_canonicalize_escaped_surrogates_from_json():
    """Escaped surrogate pairs from json.loads pass, escaped lone surrogates raise."""
    pair = json.loads('"\\ud83d\\ude00"')
    assert jcs.canonicalize(pair, utf8=False) == '"' + chr(0x1F600) + '"'
    for text in ('"\\ud800"', '"\\udc00"', '"\\ude00\\ud83d"'):
        with pytest.raises(ValueError, match="surrogates not allowed"):
            jcs.canonicalize(json.loads(text), utf8=False)


def test_canonicalize_top_level_scalars():
    """Scalars serialize on their own, without an enclosing container."""
    assert jcs.canonicalize(None) == b"null"
    assert jcs.canonicalize(True) == b"true"
    assert jcs.canonicalize(False) == b"false"
    assert jcs.canonicalize("tag") == b'"tag"'


def test_canonicalize_tuple():
    """Tuples serialize as JSON arrays."""
    assert jcs.canonicalize(("A", "tuple", 7)) == b'["A","tuple",7]'


def test_canonicalize_set():
    """Sets have no JSON form and raise TypeError."""
    with pytest.raises(TypeError):
        assert jcs.canonicalize({1, 2, 4}) == b""
