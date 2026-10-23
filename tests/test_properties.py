"""Property-based tests: invariants of RFC 8785 canonical output over generated JSON data.

Output reads back as the same doubles, and accepted integers are exact doubles that also read back
as the same integer, so different values never share canonical bytes, which signatures and hashes
over canonical JSON rely on.
"""

import json
from decimal import Decimal

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

import jcs


def is_own_shortest_form(n):
    """Return True if the exact double n reads back unchanged from its shortest decimal form.

    Below 1e21 canonical JSON writes the shortest digits of a double without exponent, so 2**60
    becomes 1152921504606847000, a different integer. From 1e21 on it writes an exponent, which
    json.loads reads as the double itself.
    """
    return abs(n) >= 1e21 or int(Decimal(repr(float(n)))) == n


FLOATS = st.floats(allow_nan=False, allow_infinity=False)
# Integers that are exact doubles and their own shortest form, the ones canonicalize accepts
CANONICAL_INTS = st.integers(-(2**53), 2**53) | FLOATS.map(int).filter(
    is_own_shortest_form
)
# Integers in and beyond the double range, most of them without an exact canonical form
ANY_INTS = (
    st.integers() | st.integers(-(2**80), 2**80) | st.integers(-(2**1100), 2**1100)
)
NUMBERS = CANONICAL_INTS | FLOATS
SCALARS = st.none() | st.booleans() | NUMBERS | st.text()
JSON = st.recursive(
    SCALARS,
    lambda children: st.lists(children) | st.dictionaries(st.text(), children),
    max_leaves=20,
)
SURROGATES = st.integers(0xD800, 0xDFFF).map(chr)


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
    """Canonical output parses back to the input, comparing numbers as doubles."""
    parsed = json.loads(jcs.canonicalize(value).decode("utf-8"), parse_int=float)
    assert normalize(parsed) == normalize(value)


@given(JSON)
def test_output_is_stable(value):
    """Canonical output read as doubles canonicalizes to the same bytes."""
    canonical = jcs.canonicalize(value)
    assert jcs.canonicalize(json.loads(canonical, parse_int=float)) == canonical


@given(JSON)
def test_utf8_modes_agree(value):
    """The str output encodes to the bytes output."""
    assert jcs.canonicalize(value, utf8=False).encode() == jcs.canonicalize(value)


@given(st.dictionaries(st.text(), SCALARS))
def test_insertion_order_ignored(dct):
    """Dict insertion order does not affect the output."""
    assert jcs.canonicalize(dict(reversed(dct.items()))) == jcs.canonicalize(dct)


# U+10000 sorts before U+E000 by UTF-16 code units (0xD800 < 0xE000), unlike by code points
@given(st.dictionaries(st.text(), st.none()))
@example({chr(0xE000): None, chr(0x10000): None})
def test_keys_sorted_by_utf16_code_units(dct):
    """Keys are sorted by UTF-16 code units (RFC 8785, section 3.2.3)."""
    keys = list(json.loads(jcs.canonicalize(dct)))
    assert keys == sorted(dct, key=utf16_units)


@given(CANONICAL_INTS)
def test_integers_read_back(n):
    """Integers with an exact canonical form are accepted and canonicalize again via json.loads."""
    canonical = jcs.canonicalize(n)
    assert json.loads(canonical) == n
    assert jcs.canonicalize(json.loads(canonical)) == canonical


@given(ANY_INTS)
@example(2**53 + 1)
@example(2**60)
@example(1152921504606847000)
@example(10**400)
def test_integers_raise_or_are_exact(n):
    """Every integer raises or is an exact double that reads back unchanged.

    Exactness keeps integers from sharing bytes with other integers or with floats.
    """
    try:
        canonical = jcs.canonicalize(n)
    except ValueError as e:
        assert "not exactly representable" in str(e)
    else:
        assert float(n) == n
        assert json.loads(canonical) == n


@given(st.text(), SURROGATES, st.text(), st.booleans())
def test_lone_surrogates_raise(prefix, surrogate, suffix, utf8):
    """Strings with a lone surrogate anywhere raise ValueError in values, keys, and lists."""
    s = prefix + surrogate + suffix
    for data in (s, {"k": s}, {s: 1}, [s]):
        with pytest.raises(ValueError, match="surrogates not allowed"):
            jcs.canonicalize(data, utf8=utf8)
