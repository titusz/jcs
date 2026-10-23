# Changelog

All notable changes to this project will be documented in this file. This project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - Unreleased

- **Breaking:** `canonicalize` raises `ValueError` for integers that IEEE 754 double precision
  cannot represent exactly (e.g. `2**53 + 1`) instead of silently rounding them, which mapped
  different values to identical output (RFC 8785, section 3.1, #1)
- Documented number handling in README
- **Breaking:** Requires Python 3.8 or newer (dropped 3.6 and 3.7)
- Migrated packaging from Poetry to uv with `uv_build` backend
- Updated CI to test Python 3.8 - 3.15 on Linux, macOS, and Windows
- Replaced black with ruff for code formatting
- Added prek quality gates (file hygiene, ruff lint, mdformat, zizmor, coverage floor) and
  Dependabot

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
