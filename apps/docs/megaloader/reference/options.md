# Plugin options

Platform-specific parameters for authentication and configuration.

## Credential precedence

All plugins follow this pattern:

1. **Explicit kwargs** (highest priority) - passed directly to `extract()`
2. **Environment variables** (fallback) - loaded from system environment
3. **Graceful failure** - plugins work without credentials when possible

**Example:**

```python
import os
import megaloader as mgl

os.environ["PIXIV_PHPSESSID"] = "env_value"
mgl.extract("https://www.pixiv.net/en/artworks/12345")  # Uses "env_value"

os.environ["PIXIV_PHPSESSID"] = "env_value"
mgl.extract("https://www.pixiv.net/en/artworks/12345", session_id="kwarg_value")  # Uses "kwarg_value"
```

## GoFile

### token (string, optional)

Gofile API token for authenticated access, avoiding automatic guest account
creation.

**Environment variable:** `GOFILE_TOKEN`

**How to obtain:**

1. Sign up at gofile.io
2. Go to your profile (https://gofile.io/myprofile)
3. Find the Developer information section
4. Copy the account token value

**Example:**

```python
for item in mgl.extract("https://gofile.io/d/abc123", token="your_api_token"):
    print(item.filename)
```

```python
import os

os.environ["GOFILE_TOKEN"] = "your_api_token"

for item in mgl.extract("https://gofile.io/d/abc123"):
    print(item.filename)
```

**CLI:**

```bash
megaloader extract "https://gofile.io/d/abc123" --token your_api_token
megaloader download "https://gofile.io/d/abc123" ./output --token your_api_token

# Or via environment variable:
export GOFILE_TOKEN="your_api_token"
megaloader download "https://gofile.io/d/abc123" ./output
```

Providing a token is optional. Without it, Gofile creates a guest account
automatically per session.

### password (string, optional)

Password for accessing password-protected folders.

**Environment variable:** Not supported

**Example:**

```python
for item in mgl.extract("https://gofile.io/d/abc123"):
    print(item.filename)

for item in mgl.extract("https://gofile.io/d/xyz789", password="secret"):
    print(item.filename)
```

**CLI:**

```bash
megaloader extract "https://gofile.io/d/xyz789" --password secret
megaloader download "https://gofile.io/d/xyz789" ./output --password secret
```

GoFile hashes passwords with SHA-256 before sending to the API. Invalid
passwords result in empty file lists without raising errors.

## Pixiv

### session_id (string, required for most content)

Authentication cookie for accessing artworks and user profiles.

**Environment variable:** `PIXIV_PHPSESSID`

**How to obtain:**

1. Log in to Pixiv
2. Open browser DevTools (F12)
3. Application/Storage → Cookies
4. Find `PHPSESSID`
5. Copy the value

**Example:**

```python
for item in mgl.extract(
    "https://www.pixiv.net/en/artworks/123456",
    session_id="your_session_cookie"
):
    print(item.filename)

for item in mgl.extract(
    "https://www.pixiv.net/en/users/789012",
    session_id="your_session_cookie"
):
    print(item.filename)
```

**CLI:**

```bash
export PIXIV_PHPSESSID="your_session_cookie"
megaloader download "https://www.pixiv.net/en/artworks/123456" ./output
```

Required for most content. Multi-page artworks are automatically detected. User
extraction includes profile images and all artworks.

## Rule34

### api_key (string, optional)

API key for authenticated access with higher rate limits.

**Environment variable:** `RULE34_API_KEY`

### user_id (string, optional)

User ID associated with the API key.

**Environment variable:** `RULE34_USER_ID`

**How to obtain:**

1. Create Rule34 account
2. Go to account settings
3. Generate API key
4. Note user ID from profile

**Example:**

```python
for item in mgl.extract("https://rule34.xxx/index.php?page=post&s=list&tags=cat"):
    print(item.filename)

for item in mgl.extract(
    "https://rule34.xxx/index.php?page=post&s=list&tags=cat",
    api_key="your_api_key",
    user_id="your_user_id"
):
    print(item.filename)
```

**CLI:**

```bash
export RULE34_API_KEY="your_api_key"
export RULE34_USER_ID="your_user_id"
megaloader download "https://rule34.xxx/..." ./output
```

API authentication is optional but recommended. Without credentials, the plugin
falls back to web scraping (slower). Both `api_key` and `user_id` must be
provided together.

## Security best practices

Never commit credentials to version control:

**Bad:**

```python
for item in mgl.extract(url, session_id="abc123def456"):
    pass
```

**Good:**

```python
import os
session_id = os.getenv("PIXIV_PHPSESSID")
for item in mgl.extract(url, session_id=session_id):
    pass
```

Store credentials in environment variables or `.env` files:

```bash
# .env file
PIXIV_PHPSESSID=your_session_value
RULE34_API_KEY=your_api_key
RULE34_USER_ID=your_user_id
GOFILE_TOKEN=your_api_token
```

Load them in code:

```python
from dotenv import load_dotenv
load_dotenv()
```

Rotate credentials regularly when sessions expire.
