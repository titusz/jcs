# JCS - JSON Canonicalization for Python 3

[![Tests](https://github.com/titusz/jcs/actions/workflows/tests.yml/badge.svg)](https://github.com/titusz/jcs/actions/workflows/tests.yml)

This is a Python 3 package for a [JCS (RFC 8785)](https://datatracker.ietf.org/doc/html/rfc8785)
compliant JSON canonicalization.

The main author of this code is [Anders Rundgren](https://github.com/cyberphone). The original
source code is at
[cyberphone/json-canonicalization](https://github.com/cyberphone/json-canonicalization/tree/master/python3)
including comprehensive test data.

## Installation

```bash
$ pip install jcs
```

## Using JCS

```python
import jcs
data = jcs.canonicalize({"tag": 4})
```

## Numbers

JCS serializes every JSON number as an IEEE 754 double precision value
([RFC 8785, section 3.1](https://www.rfc-editor.org/rfc/rfc8785#section-3.1)). Python `float` values
are doubles already and are serialized as is. Python `int` values have arbitrary precision, so
`canonicalize` raises a `ValueError` for any integer that a double cannot represent exactly, instead
of silently rounding it:

```python
>>> jcs.canonicalize({"id": 2**53 + 1})
Traceback (most recent call last):
  ...
ValueError: Integer 9007199254740993 is not exactly representable as IEEE 754 double ...
```

Silent rounding would let different values produce identical canonical bytes, so a signature or hash
over one value would also match the other.

Keep in mind:

- Large integers that a double represents exactly are accepted and serialized in their shortest
  form: `2**60` becomes `1152921504606847000` and `10**21` becomes `1e+21`. Python's `json.loads`
  reads `1152921504606847000` back as a different integer.
- For signed or hashed data, keep integers within the I-JSON safe range of `±(2**53 - 1)`
  ([RFC 7493, section 2.2](https://www.rfc-editor.org/rfc/rfc7493#section-2.2)) and use strings for
  large identifiers, counters, or amounts.
- To canonicalize JSON text with large integer literals the way JavaScript based implementations do
  (rounding them to the nearest double), parse integers as floats:
  `jcs.canonicalize(json.loads(text, parse_int=float))`.

The integer check is an addition to the original reference code. The serialization of all accepted
values is unchanged.

## Development

```bash
uv sync                          # Install dev dependencies
uv run prek install              # Install git hooks (quality gates on commit, tests on push)
uv run prek run --all-files      # Run all quality gates manually
uv run pytest                    # Run tests with coverage
```
