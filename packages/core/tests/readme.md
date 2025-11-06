# testing

This document explains how to run the tests and what they cover.  
All numbers are current as of 2025-11-05.

## Test inventory

| Type        | Count | Run time | Pass % | Notes          |
| ----------- | ----- | -------- | ------ | -------------- |
| Unit        | 14    | ~1 s     | 100    | No network     |
| Integration | 22    | ~3 s     | 100    | requests-mock  |
| Live        | 9     | ~17 s    | 78     | Real endpoints |

Total: 45 tests.

## Run them

```bash
# All except live
uv run pytest

# Everything including live
uv run pytest -m live

# One file
uv run pytest tests/unit/test_http.py

# With coverage
uv run pytest --cov=megaloader --cov-report=term
```

CI runs the same commands on Python 3.12 and 3.13 for every push to main and
every PR.

## What is actually tested

Unit (14)

- HTTP helper: filename extraction, headers, skip-existing, errors
- Plugin base: dataclass validation, abstract-method enforcement, config storage
- Sanitization: strip dangerous characters

Integration (22): all tests are mocked

- Bunkr: album parsing, single file, network errors, file-exists check
- PixelDrain: single file, list, proxy rotation, content verification
- Cyberdrop: album export, single file, rate-limit, download
- GoFile: token fetch, file export, password hash

Live (9): calls the actual servers, may skip if URL dead

- Bunkr: album + single file
- PixelDrain: single file, list, proxy domain switch
- Cyberdrop: album + single file
- GoFile: token fetch + folder export

Not covered yet:

- Performance benchmarks
- Extended plugins (Fanbox, Fapello, Pixiv, Rule34, etc.)
