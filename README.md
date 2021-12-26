# JCS - JSON Canonicalization for Python 3


This is a Python 3 package for a [JCS (RFC 8785)](https://datatracker.ietf.org/doc/html/rfc8785) compliant JSON canonicalization .

The main author of this code is [Anders Rundgren](https://github.com/cyberphone).
The original source code at <https://github.com/cyberphone/json-canonicalization>

## Installation


```bash
$ pip install jcs
```

## Using JCS

```python
import jcs

data = jcs.canonicalize({"tag":4})
```


## Changelog

### 0.1.0 - Unreleased

- created `jcs` package from original code

