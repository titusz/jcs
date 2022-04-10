# JCS - JSON Canonicalization for Python 3

[![Tests](https://github.com/titusz/jcs/actions/workflows/tests.yml/badge.svg)](https://github.com/titusz/jcs/actions/workflows/tests.yml)

This is a Python 3 package for
a [JCS (RFC 8785)](https://datatracker.ietf.org/doc/html/rfc8785) compliant JSON
canonicalization.

The main author of this code is [Anders Rundgren](https://github.com/cyberphone). The
original source code is
at [cyberphone/json-canonicalization](https://github.com/cyberphone/json-canonicalization/tree/master/python3)
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

## Changelog

### Unreleased
- Updated dependencies
- Fixed project subtitle

### 0.2.0 - 2022-01-19

- Removed pinning to py3
- Updated dependencies

### 0.1.0 - 2021-12-26

- created `jcs` package from original code
- added poetry based packaging
- reformated code with `black`
- add github ci testing workflow
