megaloader 0.3.0 is out.

This is the first core release since 0.2.0, four months ago. It fixes the import
on Python 3.10 and makes extraction fail loudly when a provider sends something
unexpected.

0.2.0 does not import on Python 3.10, although the package declares 3.10 as its
minimum. `error_policy.py` imported `typing.Never`, which exists only from 3.11.
It now uses `NoReturn`. I ran `import megaloader` on 3.10.22 against both
versions: 0.2.0 raises `ImportError`, 0.3.0 imports.

The bigger change is response validation. Providers sometimes answer with valid
JSON or markup in a shape the plugin did not expect. Before, that produced a
`KeyError`, a misleading exception, or an empty result that looked like a
finished extraction. Now the Bunkr, Cyberdrop, Gofile, PixelDrain, Pixiv,
Rule34, Thothub.to and Thothub.vip plugins check the shape and raise
`ExtractionError` with `category="protocol"`. Rule34 no longer ends pagination
when the API returns a non-XML page such as an outage or rate-limit notice. Only
a parsed page with no posts ends it.

Two smaller fixes: the library's `NullHandler` now sits on the `megaloader`
logger instead of `megaloader.api`, so every module has a safe default, and the
sdist now holds only the package and readme. The 0.2.0 sdist was 15 MB because
it carried tests and sample media. The old `MANIFEST.in` did nothing. The rest
is tests, docs and dependency pins.

## Breaking changes

`Response.json()` raises `ExtractionError` for a non-JSON body. It used to raise
`json.JSONDecodeError`, a `ValueError`. Code that caught `ValueError` around a
fetch must catch `MegaloaderError` instead. `ExtractionError` carries `source`,
`url`, `http_status` and `category`.

```python
# before (0.2.0)
try:
    data = response.json()
except ValueError:
    data = None

# after (0.3.0)
from megaloader.exceptions import MegaloaderError

try:
    data = response.json()
except MegaloaderError:
    data = None
```

A page the plugin cannot read now raises instead of yielding nothing. For
example, a PixelDrain page whose viewer data holds no files used to return an
empty list. It now raises `ExtractionError`. A genuinely empty album, a list
with an empty `files` array, still yields nothing. Callers that treated "no
items" as success for such pages now see an error:

```python
import megaloader as mgl
from megaloader.exceptions import ExtractionError

try:
    items = list(mgl.extract(url))
except ExtractionError as e:
    print(e.category, e.detail)
```

## Known problems

None known.

## What to do

Upgrade with `pip install -U megaloader`. If your code calls a plugin and treats
an empty result or a `ValueError` as "not found", read the breaking changes
above and test it. Report problems at
https://github.com/totallynotdavid/megaloader/issues.
