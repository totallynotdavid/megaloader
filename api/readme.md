# A simple API

FastAPI demo server that wraps the megaloader/core library. It is used in the
docs to show URL validation and file downloads.

Start the server by running:

```bash
cd api
uv sync
MEGALOADER_DEV=true python api.py
```

Server listens on http://localhost:8000.

You need to add this environment variables:

- `CORS_ORIGINS`: comma-separated list of allowed origins  
  default: `http://localhost:5173,http://127.0.0.1:5173`
- `MEGALOADER_DEV`: `true` runs the full FastAPI dev server; anything else
  deploys as a Vercel serverless function

## Endpoints

### GET /api/validate-url

Check if Megaloader supports the URL.

Query: `url` (required)

200 OK

```json
{
  "supported": true,
  "plugin": "PixelDrain",
  "domain": "pixeldrain.com"
}
```

400 Bad Request

```json
{ "detail": "Validation failed" }
```

### POST /api/download

Download the file (dev mode only).

Body:

```json
{ "url": "https://pixeldrain.com/u/example" }
```

200 OK

```json
{
  "success": true,
  "message": "Successfully downloaded from https://pixeldrain.com/u/example",
  "plugin": "PixelDrain"
}
```

400 Bad Request

```json
{ "error": "Missing url parameter" }
```
