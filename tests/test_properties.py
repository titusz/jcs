"""Property-based tests: invariants of RFC 8785 canonical output over generated JSON data.

The value preservation property implies that different values never share canonical bytes,
which signatures and hashes over canonical JSON rely on.
"""

import json

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

import jcs

FLOATS = st.floats(allow_nan=False, allow_infinity=False)
NUMBERS = st.integers(-(2**53), 2**53) | FLOATS | FLOATS.map(int)
SCALARS = st.none() | st.booleans() | NUMBERS | st.text()
JSON = st.recursive(
    SCALARS,
    lambda children: st.lists(children) | st.dictionaries(st.text(), children),
    max_leaves=20,
)
SURROGATES = st.integers(0xD800, 0xDFFF).map(chr)
# Odd integers above 2**53 have more significant bits than a double holds, large shifts also
# exceed the double range
INEXACT_INTS = st.builds(
    lambda m, shift, sign: sign * ((2 * m + 1) << shift),
    st.integers(2**52, 2**70),
    st.integers(0, 1100),
    st.sampled_from([1, -1]),
)


def normalize(value):
    """Return value with numbers as floats and booleans tagged, for type-aware JSON equality."""
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, list):
        return [normalize(v) for v in value]
    if isinstance(value, dict):
        return {k: normalize(v) for k, v in value.items()}
    return value


def utf16_units(s):
    """Return the UTF-16 code units of s, computed without a codec."""
    units = []
    for char in s:
        n = ord(char)
        if n > 0xFFFF:
            n -= 0x10000
            units += [0xD800 + (n >> 10), 0xDC00 + (n & 0x3FF)]
        else:
            units.append(n)
    return units


@given(JSON)
def test_output_preserves_value(value):
    parsed = json.loads(jcs.canonicalize(value).decode("utf-8"), parse_int=float)
    assert normalize(parsed) == normalize(value)


@given(JSON)
def test_output_is_stable(value):
    canonical = jcs.canonicalize(value)
    assert jcs.canonicalize(json.loads(canonical, parse_int=float)) == canonical


@given(JSON)
def test_utf8_modes_agree(value):
    assert jcs.canonicalize(value, utf8=False).encode() == jcs.canonicalize(value)


@given(st.dictionaries(st.text(), SCALARS))
def test_insertion_order_ignored(dct):
    assert jcs.canonicalize(dict(reversed(dct.items()))) == jcs.canonicalize(dct)


# U+10000 sorts before U+E000 by UTF-16 code units (0xD800 < 0xE000), unlike by code points
@given(st.dictionaries(st.text(), st.none()))
@example({chr(0xE000): None, chr(0x10000): None})
def test_keys_sorted_by_utf16_code_units(dct):
    keys = list(json.loads(jcs.canonicalize(dct)))
    assert keys == sorted(dct, key=utf16_units)


@given(INEXACT_INTS)
def test_inexact_integers_raise(n):
    with pytest.raises(ValueError, match="not exactly representable"):
        jcs.canonicalize(n)


@given(st.text(), SURROGATES, st.text(), st.booleans())
def test_lone_surrogates_raise(prefix, surrogate, suffix, utf8):
    s = prefix + surrogate + suffix
    for data in (s, {"k": s}, {s: 1}, [s]):
        with pytest.raises(ValueError, match="surrogates not allowed"):
            jcs.canonicalize(data, utf8=utf8)
