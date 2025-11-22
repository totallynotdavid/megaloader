---
title: Plugin options
description: Authentication options and platform-specific parameters
outline: [2, 3]
prev:
  text: "Supported platforms"
  link: "/plugins/platforms"
next:
  text: "Creating plugins"
  link: "/plugins/creating"
---

# Plugin options

Some platforms need extra parameters for authentication or password protection.
These are passed as kwargs to `extract()` and follow a consistent credential
precedence pattern.

## Credential precedence

All plugins follow this pattern:

1. **Explicit kwargs** (highest priority) - passed directly to `extract()`
2. **Environment variables** (fallback) - loaded from system environment
3. **Graceful failure** - plugins work without credentials when possible

This lets you hardcode credentials for testing, use environment variables in
production, and share code without exposing secrets.

**Example:**

```python
import os
import megaloader as mgl

# Scenario 1: Only environment variable
os.environ["FANBOX_SESSION_ID"] = "env_value"
mgl.extract("https://creator.fanbox.cc")  # Uses "env_value"

# Scenario 2: Both env var and kwarg (kwarg wins)
os.environ["FANBOX_SESSION_ID"] = "env_value"
mgl.extract("https://creator.fanbox.cc", session_id="kwarg_value")  # Uses "kwarg_value"
```

## GoFile

### password (string, optional)

Password for accessing password-protected folders.

**Environment variable:** Not supported (passwords are folder-specific)

**Example:**

```python
# Public folder
for item in mgl.extract("https://gofile.io/d/abc123"):
    print(item.filename)

# Password-protected
for item in mgl.extract("https://gofile.io/d/xyz789", password="secret"):
    print(item.filename)
```

**CLI:**

```bash
megaloader download "https://gofile.io/d/xyz789" ./output --password secret
```

**Notes:** GoFile hashes passwords with SHA-256 before sending to the API.
Invalid passwords result in empty file lists without raising errors.

## Fanbox

### session_id (string, required for most content)

Authentication cookie for accessing creator content.

**Environment variable:** `FANBOX_SESSION_ID`

**How to obtain:**

1. Log in to Fanbox
2. Open browser DevTools (F12)
3. Application/Storage → Cookies
4. Find `FANBOXSESSID`
5. Copy the value

**Example:**

```python
# Explicit parameter
for item in mgl.extract(
    "https://creator.fanbox.cc",
    session_id="your_session_cookie"
):
    print(item.filename)

# Environment variable
import os
os.environ["FANBOX_SESSION_ID"] = "your_session_cookie"

for item in mgl.extract("https://creator.fanbox.cc"):
    print(item.filename)
```

**CLI:**

```bash
export FANBOX_SESSION_ID="your_session_cookie"
megaloader download "https://creator.fanbox.cc" ./output
```

**Notes:** Most creator content requires authentication. Session cookies expire
periodically. Without authentication, you'll get 403 errors.

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
# Single artwork
for item in mgl.extract(
    "https://www.pixiv.net/en/artworks/123456",
    session_id="your_session_cookie"
):
    print(item.filename)

# User profile
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

**Notes:** Required for most content. Multi-page artworks are automatically
detected. User extraction includes profile images and all artworks.

## Rule34

### api_key (string, optional)

API key for authenticated access with higher rate limits.

**Environment variable:** `RULE34_API_KEY`

### user_id (string, optional)

User ID associated with the API key.

**Environment variable:** `RULE34_USER_ID`

**How to obtain:**

1. Create a Rule34 account
2. Go to account settings
3. Generate an API key
4. Note your user ID from your profile

**Example:**

```python
# Without authentication (slower, web scraping)
for item in mgl.extract("https://rule34.xxx/index.php?page=post&s=list&tags=cat"):
    print(item.filename)

# With API authentication (faster, more reliable)
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

**Notes:** API authentication is optional but recommended. Without credentials,
the plugin falls back to web scraping (slower). Both `api_key` and `user_id`
must be provided together.

## Security best practices

Never commit credentials to version control or hard-code them in your
application.

**Bad:**

```python
for item in mgl.extract(url, session_id="abc123def456"):
    pass
```

**Good:**

```python
import os
session_id = os.getenv("FANBOX_SESSION_ID")
for item in mgl.extract(url, session_id=session_id):
    pass
```

Store credentials in environment variables or `.env` files:

```bash
# .env file
FANBOX_SESSION_ID=your_session_value
PIXIV_PHPSESSID=your_session_value
RULE34_API_KEY=your_api_key
RULE34_USER_ID=your_user_id
```

Load them in your code:

```python
from dotenv import load_dotenv
load_dotenv()

# Credentials now available via os.getenv()
```

Rotate credentials regularly when sessions expire or you change passwords.
