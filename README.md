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
`canonicalize` accepts an integer only if a double represents it exactly and its canonical form
reads back as the same integer. It raises a `ValueError` for any other integer, instead of silently
rounding it:

```python
>>> jcs.canonicalize({"id": 2**53 + 1})
Traceback (most recent call last):
  ...
ValueError: Integer 9007199254740993 is not exactly representable in canonical JSON ...
```

Silent rounding would let different values produce identical canonical bytes, so a signature or hash
over one value would also match the other. An accepted integer equals its double, so no other
integer or float shares its canonical bytes, and `json.loads` reads them back as the same integer.

Keep in mind:

- Canonical JSON writes the shortest digits of the nearest double. `2**60` is an exact double, but
  it serializes as `1152921504606847000`, a different integer, so `canonicalize(2**60)` raises.
  `canonicalize(1152921504606847000)` raises too, because a double cannot represent it.
- From `1e21` on, numbers are written with an exponent (`10**21` becomes `1e+21`) and `json.loads`
  reads them as `float`, so every integer that a double represents exactly is accepted.
- For signed or hashed data, keep integers within the I-JSON safe range of `±(2**53 - 1)`
  ([RFC 7493, section 2.2](https://www.rfc-editor.org/rfc/rfc7493#section-2.2)) and use strings for
  large identifiers, counters, or amounts.
- Canonical JSON from JavaScript and other double based implementations can contain integers like
  `1152921504606847000`, which `json.loads` reads as integers that a double cannot represent. To
  canonicalize such text the way those implementations do, and the way jcs 0.2 did, parse integers
  as floats: `jcs.canonicalize(json.loads(text, parse_int=float))`.

The integer check is an addition to the original reference code. The serialization of all accepted
values is unchanged.

## Development

```bash
uv sync                          # Install dev dependencies
uv run prek install              # Install git hooks (quality gates on commit, tests on push)
uv run prek run --all-files      # Run all quality gates manually
uv run pytest --cov=jcs          # Run tests with coverage floor
```

## Releasing

1. Set the version in `pyproject.toml` and `jcs/__init__.py` and date the CHANGELOG entry
2. Commit, then push a matching tag: `git tag v0.3.0 && git push origin v0.3.0`

The [release workflow](https://github.com/titusz/jcs/blob/main/.github/workflows/release.yml) runs
the quality gates and tests, checks that the tag matches the package version, builds, and publishes
to PyPI via trusted publishing with attestations.
