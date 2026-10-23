"""Conformance tests against RFC 8785 Appendix B and the upstream reference test data.

Upstream test data: https://github.com/cyberphone/json-canonicalization (see tests/data/README.md)
"""

import hashlib
import json
import math
import struct
from pathlib import Path

import pytest

import jcs

DATA = Path(__file__).parent / "data"
FIXTURES = sorted(p.stem for p in (DATA / "input").glob("*.json"))

# RFC 8785, Appendix B: ECMAScript-compatible number serialization samples
APPENDIX_B = [
    ("0000000000000000", "0"),
    ("8000000000000000", "0"),
    ("0000000000000001", "5e-324"),
    ("8000000000000001", "-5e-324"),
    ("7fefffffffffffff", "1.7976931348623157e+308"),
    ("ffefffffffffffff", "-1.7976931348623157e+308"),
    ("4340000000000000", "9007199254740992"),
    ("c340000000000000", "-9007199254740992"),
    ("4430000000000000", "295147905179352830000"),
    ("44b52d02c7e14af5", "9.999999999999997e+22"),
    ("44b52d02c7e14af6", "1e+23"),
    ("44b52d02c7e14af7", "1.0000000000000001e+23"),
    ("444b1ae4d6e2ef4e", "999999999999999700000"),
    ("444b1ae4d6e2ef4f", "999999999999999900000"),
    ("444b1ae4d6e2ef50", "1e+21"),
    ("3eb0c6f7a0b5ed8c", "9.999999999999997e-7"),
    ("3eb0c6f7a0b5ed8d", "0.000001"),
    ("41b3de4355555553", "333333333.3333332"),
    ("41b3de4355555554", "333333333.33333325"),
    ("41b3de4355555555", "333333333.3333333"),
    ("41b3de4355555556", "333333333.3333334"),
    ("41b3de4355555557", "333333333.33333343"),
    ("becbf647612f3696", "-0.0000033333333333333333"),
    ("43143ff3c1cb0959", "1424953923781206.2"),
]

# RFC 8785, Appendix B: values out of range for JSON (NaN, Infinity)
APPENDIX_B_OUT_OF_RANGE = ["7fffffffffffffff", "7ff0000000000000"]

# Edge-case values that open upstream's ES6 number test file (testdata/numgen.go)
# fmt: off
ES6_STATIC = (
    0x0000000000000000, 0x8000000000000000, 0x0000000000000001, 0x8000000000000001,
    0xc46696695dbd1cc3, 0xc43211ede4974a35, 0xc3fce97ca0f21056, 0xc3c7213080c1a6ac,
    0xc39280f39a348556, 0xc35d9b1f5d20d557, 0xc327af4c4a80aaac, 0xc2f2f2a36ecd5556,
    0xc2be51057e155558, 0xc28840d131aaaaac, 0xc253670dc1555557, 0xc21f0b4935555557,
    0xc1e8d5d42aaaaaac, 0xc1b3de4355555556, 0xc17fca0555555556, 0xc1496e6aaaaaaaab,
    0xc114585555555555, 0xc0e046aaaaaaaaab, 0xc0aa0aaaaaaaaaaa, 0xc074d55555555555,
    0xc040aaaaaaaaaaab, 0xc00aaaaaaaaaaaab, 0xbfd5555555555555, 0xbfa1111111111111,
    0xbf6b4e81b4e81b4f, 0xbf35d867c3ece2a5, 0xbf0179ec9cbd821e, 0xbecbf647612f3696,
    0xbe965e9f80f29212, 0xbe61e54c672874db, 0xbe2ca213d840baf8, 0xbdf6e80fe033c8c6,
    0xbdc2533fe68fd3d2, 0xbd8d51ffd74c861c, 0xbd5774ccac3d3817, 0xbd22c3d6f030f9ac,
    0xbcee0624b3818f79, 0xbcb804ea293472c7, 0xbc833721ba905bd3, 0xbc4ebe9c5db3c61e,
    0xbc18987d17c304e5, 0xbbe3ad30dfcf371d, 0xbbaf7b816618582f, 0xbb792f9ab81379bf,
    0xbb442615600f9499, 0xbb101e77800c76e1, 0xbad9ca58cce0be35, 0xbaa4a1e0a3e6fe90,
    0xba708180831f320d, 0xba3a68cd9e985016, 0x446696695dbd1cc3, 0x443211ede4974a35,
    0x43fce97ca0f21056, 0x43c7213080c1a6ac, 0x439280f39a348556, 0x435d9b1f5d20d557,
    0x4327af4c4a80aaac, 0x42f2f2a36ecd5556, 0x42be51057e155558, 0x428840d131aaaaac,
    0x4253670dc1555557, 0x421f0b4935555557, 0x41e8d5d42aaaaaac, 0x41b3de4355555556,
    0x417fca0555555556, 0x41496e6aaaaaaaab, 0x4114585555555555, 0x40e046aaaaaaaaab,
    0x40aa0aaaaaaaaaaa, 0x4074d55555555555, 0x4040aaaaaaaaaaab, 0x400aaaaaaaaaaaab,
    0x3fd5555555555555, 0x3fa1111111111111, 0x3f6b4e81b4e81b4f, 0x3f35d867c3ece2a5,
    0x3f0179ec9cbd821e, 0x3ecbf647612f3696, 0x3e965e9f80f29212, 0x3e61e54c672874db,
    0x3e2ca213d840baf8, 0x3df6e80fe033c8c6, 0x3dc2533fe68fd3d2, 0x3d8d51ffd74c861c,
    0x3d5774ccac3d3817, 0x3d22c3d6f030f9ac, 0x3cee0624b3818f79, 0x3cb804ea293472c7,
    0x3c833721ba905bd3, 0x3c4ebe9c5db3c61e, 0x3c18987d17c304e5, 0x3be3ad30dfcf371d,
    0x3baf7b816618582f, 0x3b792f9ab81379bf, 0x3b442615600f9499, 0x3b101e77800c76e1,
    0x3ad9ca58cce0be35, 0x3aa4a1e0a3e6fe90, 0x3a708180831f320d, 0x3a3a68cd9e985016,
    0x4024000000000000, 0x4014000000000000, 0x3fe0000000000000, 0x3fa999999999999a,
    0x3f747ae147ae147b, 0x3f40624dd2f1a9fc, 0x3f0a36e2eb1c432d, 0x3ed4f8b588e368f1,
    0x3ea0c6f7a0b5ed8d, 0x3e6ad7f29abcaf48, 0x3e35798ee2308c3a, 0x3ed539223589fa95,
    0x3ed4ff26cd5a7781, 0x3ed4f95a762283ff, 0x3ed4f8c60703520c, 0x3ed4f8b72f19cd0d,
    0x3ed4f8b5b31c0c8d, 0x3ed4f8b58d1c461a, 0x3ed4f8b5894f7f0e, 0x3ed4f8b588ee37f3,
    0x3ed4f8b588e47da4, 0x3ed4f8b588e3849c, 0x3ed4f8b588e36bb5, 0x3ed4f8b588e36937,
    0x3ed4f8b588e368f8, 0x3ed4f8b588e368f1, 0x3ff0000000000000, 0xbff0000000000000,
    0xbfeffffffffffffa, 0xbfeffffffffffffb, 0x3feffffffffffffa, 0x3feffffffffffffb,
    0x3feffffffffffffc, 0x3feffffffffffffe, 0xbfefffffffffffff, 0xbfefffffffffffff,
    0x3fefffffffffffff, 0x3fefffffffffffff, 0x3fd3333333333332, 0x3fd3333333333333,
    0x3fd3333333333334, 0x0010000000000000, 0x000ffffffffffffd, 0x000fffffffffffff,
    0x7fefffffffffffff, 0xffefffffffffffff, 0x4340000000000000, 0xc340000000000000,
    0x4430000000000000, 0x44b52d02c7e14af5, 0x44b52d02c7e14af6, 0x44b52d02c7e14af7,
    0x444b1ae4d6e2ef4e, 0x444b1ae4d6e2ef4f, 0x444b1ae4d6e2ef50, 0x3eb0c6f7a0b5ed8c,
    0x3eb0c6f7a0b5ed8d, 0x41b3de4355555553, 0x41b3de4355555554, 0x41b3de4355555555,
    0x41b3de4355555556, 0x41b3de4355555557, 0xbecbf647612f3696, 0x43143ff3c1cb0959,
)
# fmt: on

# SHA-256 of the first N lines of upstream's ES6 number test file (testdata/README.md)
ES6_CHECKSUMS = {
    1000: "be18b62b6f69cdab33a7e0dae0d9cfa869fda80ddc712221570f9f40a5878687",
    10000: "b9f7a8e75ef22a835685a52ccba7f7d6bdc99e34b010992cbc5864cd12be6892",
    100000: "22776e6d4b49fa294a0d0f349268e5c28808fe7e0cb2bcbe28f63894e494d4c7",
}


def bits_to_float(bits):
    """Return the IEEE 754 double with the 64-bit pattern `bits`."""
    return struct.unpack("<d", struct.pack("<Q", bits))[0]


def float_to_bits(value):
    """Return the 64-bit IEEE 754 pattern of the double `value`."""
    return struct.unpack("<Q", struct.pack("<d", value))[0]


def es6_test_values():
    """Yield the doubles of upstream's ES6 number test file in order (port of numgen.go)."""
    for bits in ES6_STATIC:
        yield bits_to_float(bits)
    for i in range(2000):
        yield bits_to_float(0x0010000000000000 + i)
    block = bytes(32)
    while True:
        block = hashlib.sha256(block).digest()
        for (value,) in struct.iter_unpack("<d", block):
            if value != 0 and math.isfinite(value):
                yield value


@pytest.mark.parametrize(("ieee_hex", "expected"), APPENDIX_B)
def test_rfc8785_appendix_b(ieee_hex, expected):
    assert jcs.canonicalize(bits_to_float(int(ieee_hex, 16))) == expected.encode()


@pytest.mark.parametrize("ieee_hex", APPENDIX_B_OUT_OF_RANGE)
def test_rfc8785_appendix_b_out_of_range(ieee_hex):
    with pytest.raises(ValueError):
        jcs.canonicalize(bits_to_float(int(ieee_hex, 16)))


def test_upstream_fixtures_present():
    assert FIXTURES == ["arrays", "french", "structures", "unicode", "values", "weird"]


@pytest.mark.parametrize("name", FIXTURES)
def test_upstream_fixture(name):
    data = json.loads((DATA / "input" / f"{name}.json").read_bytes())
    expected = (DATA / "output" / f"{name}.json").read_bytes()
    assert jcs.canonicalize(data) == expected
    assert bytes.fromhex((DATA / "outhex" / f"{name}.txt").read_text()) == expected


def test_es6_number_test_file_checksums():
    digest = hashlib.sha256()
    values = es6_test_values()
    for line_count in range(1, max(ES6_CHECKSUMS) + 1):
        value = next(values)
        number = jcs.canonicalize(value).decode()
        digest.update(f"{float_to_bits(value):x},{number}\n".encode())
        if line_count in ES6_CHECKSUMS:
            assert digest.hexdigest() == ES6_CHECKSUMS[line_count], line_count
