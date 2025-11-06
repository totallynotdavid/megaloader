# Megaloader API

Simple Vercel API for URL validation using the Megaloader library.

## Endpoints

### GET /api/validate-url

Validate if a URL is supported by Megaloader.

**Query Parameters:**
- `url` (required): The URL to validate

**Response:**
```json
{
  "supported": true,
  "plugin": "PixelDrain",
  "domain": "pixeldrain.com"
}
```

**Error Response:**
```json
{
  "error": "Missing url parameter"
}
```

## Deployment to Vercel

1. Install Vercel CLI: `npm i -g vercel`
2. Deploy: `cd api && vercel --prod`
3. Note the deployment URL (e.g., `https://megaloader-api.vercel.app`)

## Local Development

```bash
cd api
uv sync
uv run python -c "
# Test the handler
from validate_url import handler

event = {'queryStringParameters': {'url': 'https://pixeldrain.com/u/test'}}
result = handler(event, None)
print('Status:', result['statusCode'])
print('Body:', result['body'])
"
```

## Integration

Update the docs demo page (`docs/demo.md`) to use your deployed API URL:

```javascript
const response = await fetch(`https://your-api-url.vercel.app/api/validate-url?url=${encodeURIComponent(url.value)}`)
```