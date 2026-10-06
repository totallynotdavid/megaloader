# Errors

A failed operation raises `UnsupportedDomainError` or `ExtractionError`, and
both derive from `megaloader.exceptions.MegaloaderError`. Invalid input raises
the built-in `ValueError` or `TypeError`, which `except MegaloaderError` does
not catch.

| Exception                | Raised when                                                                                                 |
| ------------------------ | ----------------------------------------------------------------------------------------------------------- |
| `ValueError`             | The URL is empty or has no domain, the `plugin` name is unknown, or a plugin rejects the URL shape.         |
| `TypeError`              | `plugin` is a class that does not inherit from `BasePlugin`.                                                |
| `UnsupportedDomainError` | No plugin is registered for the URL's domain. The `domain` attribute holds it.                              |
| `ExtractionError`        | A request failed, the platform answered with an error, or the response did not have the expected structure. |

`extract()` is a generator, so all of them surface when you iterate:

```python
import megaloader as mgl

try:
    items = list(mgl.extract("https://example.com/a/abc123"))
except mgl.UnsupportedDomainError as e:
    print("no plugin for", e.domain)
except ValueError as e:
    print("bad input:", e)
except mgl.ExtractionError as e:
    print("failed:", e.category, e)
```

Output for each case:

```text
UnsupportedDomainError  No plugin found for domain: example.com
ValueError              Invalid URL: Could not parse domain from 'not a url'
ValueError              Unrecognized Bunkr URL, expected /a/ or /f/: https://bunkr.si/x/nothing
ExtractionError         bunkr request failed (404): https://bunkr.si/a/doesnotexist1
TypeError               plugin class must inherit from BasePlugin
```

Any other exception a plugin raises, except a `ValueError`, which passes through
unchanged, is wrapped in an `ExtractionError` with category `unknown`. The
original exception is on `__cause__` and on `.cause`.

## ExtractionError

| Attribute         | Meaning                                                              |
| ----------------- | -------------------------------------------------------------------- |
| `detail`          | The message. `str(error)` returns it.                                |
| `source`          | Lowercase plugin name, such as `bunkr`.                              |
| `url`             | The URL that failed.                                                 |
| `http_status`     | The HTTP status, when the failure was an HTTP response.              |
| `provider_status` | The status string a platform API returned, such as `error-notfound`. |
| `category`        | One of the categories below.                                         |
| `cause`           | The underlying exception, or `None`.                                 |

Branch on `category` and not on the message text:

| Category     | Set when                                                                                                       |
| ------------ | -------------------------------------------------------------------------------------------------------------- |
| `rate_limit` | HTTP `429`, or the provider status `error-ratelimit`.                                                          |
| `auth`       | HTTP `401`.                                                                                                    |
| `access`     | HTTP `403` or `404`, or the provider status `error-notpremium`, `error-notfound`, or `error-passwordrequired`. |
| `request`    | Any other HTTP error status.                                                                                   |
| `network`    | The connection failed.                                                                                         |
| `timeout`    | The request timed out.                                                                                         |
| `protocol`   | The response was not valid JSON or lacked the fields the plugin needs.                                         |
| `unknown`    | Anything else.                                                                                                 |

A failure that matches no row of the status mapping, for example a provider
status the plugin does not recognise, is `unknown`.

```python
try:
    items = list(mgl.extract(url))
except mgl.ExtractionError as e:
    if e.category == "rate_limit":
        time.sleep(60)
    elif e.category == "access":
        print("missing, private, or password protected:", e.url)
    else:
        raise
```

## Partial results

Items are yielded as they are found. An error in the middle of a collection
raises from the iteration after the earlier items were already yielded. Collect
as you go to keep them:

```python
items = []
try:
    for item in mgl.extract(url):
        items.append(item)
except mgl.ExtractionError as e:
    print(f"stopped after {len(items)} items: {e}")
```

Pixiv is the exception for artworks without an original image. In a user gallery
the plugin skips the artwork and logs a warning. An artwork URL for such an
artwork raises an `ExtractionError` with category `protocol`.
