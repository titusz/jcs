# Changelog

All notable changes to this project will be documented in this file. This project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - Unreleased

- **Breaking:** `canonicalize` raises `ValueError` for integers that IEEE 754 double precision
  cannot represent exactly (e.g. `2**53 + 1`) instead of silently rounding them, which mapped
  different values to identical output (RFC 8785, section 3.1, #1). Thanks to jmgurney for the
  report and MoltyCel for the analysis
- **Breaking:** `canonicalize(obj, utf8=False)` raises `UnicodeEncodeError` (a `ValueError`) for
  strings with lone surrogates instead of returning them, like the default `utf8=True` mode already
  did (RFC 8785, section 3.2.2.2)
- **Breaking:** `canonicalize` raises `TypeError` for dict keys that are not strings instead of an
  accidental `AttributeError`. Converting them like `json.dumps` would map `{1: "a"}` and
  `{"1": "a"}` to identical output
- Documented number handling in README
- Added the missing license files to the repository and distributions: `LICENSE` (Apache-2.0) and
  `LICENSE.PSF`, because `jcs/_jcs.py` is derived from CPython's `json/encoder.py`
- **Breaking:** Requires Python 3.8 or newer (dropped 3.6 and 3.7)
- Migrated packaging from Poetry to uv with `uv_build` backend
- Updated CI to test Python 3.8 - 3.15 on Linux, macOS, and Windows
- Replaced black with ruff for code formatting
- Added a release workflow: pushing a version tag runs the quality gates and tests, then publishes
  to PyPI via trusted publishing with attestations
- Added prek quality gates (file hygiene, ruff lint, mdformat, zizmor, coverage floor) and
  Dependabot
- Added conformance tests: RFC 8785 Appendix B number samples, upstream reference test files, and
  checksums of the first 100,000 values of upstream's ES6 number test file
- Added property-based tests with Hypothesis: value preservation, stable output, UTF-16 key order,
  insertion order independence, and rejection of inexact integers and lone surrogates

## [0.2.1] - 2022-04-10

- Fixed project subtitle
- Moved changelog
- Updated dependencies

## [0.2.0] - 2022-01-19

- Removed pinning to py3
- Updated dependencies

### [0.1.0] - 2021-12-26

- Created `jcs` package from original code
- Added poetry based packaging
- Reformated code with `black`
- Add GitHub CI testing workflow
