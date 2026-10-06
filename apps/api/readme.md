# Megaloader API

A FastAPI server built on the `megaloader` library. It accepts a link, extracts
the files behind it, and returns the file, or a ZIP archive when there are
several. It runs the demo on the documentation site and is deployed to Vercel.

The server handles four platforms: Bunkr, PixelDrain, Cyberdrop, and GoFile. It
refuses downloads over a size limit and requests over a rate limit.

## Run it

From the repository root:

```bash
mise run sync        # install the API's dependencies
mise run api-serve   # uvicorn index:app --reload, in apps/api
```

Without mise:

```bash
cd apps/api
uv sync --extra dev
uv run uvicorn index:app --reload
```

The server listens on `http://localhost:8000`. `/docs` serves Swagger UI and
`/redoc` serves ReDoc.

```console
$ curl -s localhost:8000/
{"status":"online","service":"Megaloader API","version":"2.0.0","limits":{"max_size_mb":4.0,"max_files":50},"endpoints":{"validate":"POST /validate","download":"POST /download"},"docs":"/docs"}
```

## Endpoints

### `GET /`

Returns the service status and the active size and file limits.

### `POST /validate`

Checks that a URL's domain is allowed and has a plugin.

```console
$ curl -s localhost:8000/validate -H 'content-type: application/json' \
    -d '{"url": "https://pixeldrain.com/u/abc123"}'
{"supported":true,"domain":"pixeldrain.com","plugin":"PixelDrain"}
```

### `POST /download`

Extracts the URL and downloads its files. The body is `{"url": "..."}`.

- Total size within the limit: one file is returned as is, several files as
  `<domain>_download.zip`.
- Total size over the limit: a JSON preview, with status `200` and no file
  content.

```json
{
  "total_size_bytes": 5242880,
  "total_size_mb": 5.0,
  "file_count": 10,
  "files": [
    {
      "filename": "file1.jpg",
      "size_bytes": 524288,
      "size_mb": 0.5,
      "url": "https://..."
    }
  ],
  "exceeds_limit": true,
  "limit_mb": 4.0,
  "message": "Size 5.00 MB exceeds 4.0MB limit"
}
```

A file that fails to download is left out of the response. When every file
fails, the status is `500`.

The server reads each file's size with a `HEAD` request. A file whose size it
cannot read counts as 0 bytes, and the limit is enforced again on the bytes it
streams.

## Status codes

| Status | When                                                                                |
| ------ | ----------------------------------------------------------------------------------- |
| `400`  | The URL is malformed, is not HTTP(S), or carries credentials.                       |
| `401`  | The source requires authentication.                                                 |
| `403`  | The domain is not in the allowed list.                                              |
| `404`  | The source content is missing or access is denied.                                  |
| `413`  | The content grew past the size limit while downloading.                             |
| `422`  | The body is invalid, or the URL holds more than `API_MAX_FILES` files, or no files. |
| `429`  | The rate limit applies, or the source rate-limited the server.                      |
| `502`  | The source is unreachable or sent an unexpected response.                           |
| `504`  | The source timed out.                                                               |
| `500`  | Any other failure.                                                                  |

The server's own rate limit response carries a `Retry-After` header.

The allowed domains are `bunkr.si`, `bunkr.la`, `bunkr.is`, `bunkr.ru`,
`bunkr.su`, `pixeldrain.com`, `cyberdrop.cr`, `cyberdrop.me`, `cyberdrop.to`,
and `gofile.io`. The host must match one of them exactly.

## Configuration

Environment variables. Every one is optional.

| Variable                   | Default                             | Meaning                                                        |
| -------------------------- | ----------------------------------- | -------------------------------------------------------------- |
| `API_MAX_SIZE_MB`          | `4.0`                               | Total size limit per request.                                  |
| `API_MAX_FILES`            | `50`                                | Most files a request may extract.                              |
| `API_SIZE_CHECK_TIMEOUT`   | `5`                                 | Seconds for each `HEAD` size check.                            |
| `API_DOWNLOAD_TIMEOUT`     | `30`                                | Seconds for each file download request.                        |
| `UPSTASH_REDIS_REST_URL`   |                                     | Upstash Redis REST URL for rate limiting.                      |
| `UPSTASH_REDIS_REST_TOKEN` |                                     | Upstash Redis REST token.                                      |
| `API_RATE_LIMIT_REQUESTS`  | `10`                                | Requests allowed per window and caller.                        |
| `API_RATE_LIMIT_WINDOW`    | `60`                                | Window length in seconds.                                      |
| `API_CORS_ORIGINS`         | `*`                                 | Comma-separated allowed origins.                               |
| `API_TRUST_PROXY`          | `true` on Vercel, otherwise `false` | Read the caller from `X-Forwarded-For`.                        |
| `API_LOG_LEVEL`            | `INFO`                              | Log level.                                                     |
| `API_LOG_FORMAT`           | `json`                              | `json` or `text`.                                              |
| `ENV`                      |                                     | `production` leaves tracebacks out of extraction-failure logs. |

[`apps/api/.env.example`](.env.example) lists them with comments.

Rate limiting needs both Upstash variables. Without them every request is
allowed. The limit is per caller IP. With `API_TRUST_PROXY` on, the caller is
the left-most `X-Forwarded-For` entry, so enable it only behind a proxy that
sets the header, since clients can forge it.

Credentialed CORS requests are allowed only when `API_CORS_ORIGINS` is an
explicit list. With `*` the server sends no `Access-Control-Allow-Credentials`.

## Download safety

The server fetches download URLs that come from third-party pages. Before each
request, and at each redirect (at most 5), it resolves the host and refuses
loopback, private, link-local, and other non-public addresses. It resolves the
name once for the check and the connection resolves it again, so the check does
not stop DNS rebinding. Redirects to another origin drop `Authorization` and
`Cookie` headers.

## Tests

```bash
mise run test-api
```

## Deploy

```bash
mise run api-deploy   # vercel --prod, in apps/api
```

## License

Apache-2.0, as the rest of the repository.
