# [api]: a megaloader demo

A FastAPI server built on the megaloader core library. It validates URLs and
returns downloadable content through simple HTTP endpoints. This demo is used in
the project's documentation and intentionally supports fewer platforms, with
limits on size, file count, request rate, and request timeouts.

## Running locally

```bash
cd api
uv sync
uvicorn api.main:app --reload
```

The server runs on `http://localhost:8000`. Open `/docs` for Swagger or `/redoc`
for ReDoc. A hosted version is deployed on Vercel; configuration is defined in
[`vercel.json`](../vercel.json) at the repository root.

## Supported platforms

The demo enables a restricted set of stable platforms from the core library.

| Platform   | Domains                | Supports       |
| ---------- | ---------------------- | -------------- |
| Bunkr      | bunkr.{si,la,is,ru,su} | Albums, files  |
| PixelDrain | pixeldrain.com         | Lists, files   |
| Cyberdrop  | cyberdrop.{cr,me,to}   | Albums, files  |
| GoFile     | gofile.io              | Folders, files |

## Environment variables

The API is configured through environment variables; defaults allow it to run
without additional setup.

Size-related limits come from two settings: `API_MAX_SIZE_MB`, which caps the
total upload size (default is 4 MB), and `API_MAX_FILES`, which restricts the
number of files per request (default is 50). Logging can be tuned with
`API_LOG_LEVEL` (defaulting to `INFO`) and `API_LOG_FORMAT` (`json` by default).

CORS is configured through `API_CORS_ORIGINS`, which accepts a comma-separated
list of allowed origins and defaults to allowing all (`*`). Rate limiting is
handled by `API_RATE_LIMIT_REQUESTS` and `API_RATE_LIMIT_WINDOW`; by default,
the API allows 10 requests every 60 seconds.

Finally, when checking file sizes, HEAD requests use a timeout controlled by
`API_HEAD_REQUEST_TIMEOUT`, which is set to 10 seconds by default.

Example:

```bash
API_MAX_SIZE_MB=4.0
API_MAX_FILES=50
API_LOG_LEVEL=INFO
API_CORS_ORIGINS=https://example.com
API_RATE_LIMIT_REQUESTS=10
API_RATE_LIMIT_WINDOW=60
API_HEAD_REQUEST_TIMEOUT=10
```

## Endpoints

Only the primary endpoints are described here. Full schema and examples are
available through Swagger and ReDoc.

`GET /`

Returns basic service information and active limits.

`POST /validate`

Validates a submitted URL and reports whether the domain is supported. Example
request:

```json
{ "url": "https://pixeldrain.com/u/abc123" }
```

`POST /download`

Extracts content from a URL. If the total size remains within configured limits,
the response contains the file or a ZIP archive. If limits are exceeded,
metadata is returned instead of file content.

Example oversized response:

```json
{
  "total_size_mb": 5.0,
  "file_count": 10,
  "files": [{ "filename": "file1.jpg", "size_mb": 0.5 }],
  "exceeds_limit": true,
  "limit_mb": 4.0
}
```

Possible error codes include 400 for unsupported domains, 422 for invalid
requests, 429 for rate limits, and 500 for extraction failures.

---

Licensing follows the main project's LICENSE file.
