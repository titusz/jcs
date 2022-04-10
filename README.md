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
