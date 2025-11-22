---
title: Plugin-specific options
description: Authentication options, passwords, and platform-specific parameters for Megaloader plugins with security best practices.
outline: [2, 3]
prev:
  text: 'Supported Platforms'
  link: '/plugins/supported-platforms'
next:
  text: 'Creating Plugins'
  link: '/plugins/creating-plugins'
---

# Plugin-Specific Options

Some platforms require or support additional parameters for authentication, password protection, or enhanced functionality. These options are passed as keyword arguments to the `extract()` function.

[[toc]]

## Credential handling convention

Megaloader follows a consistent credential precedence pattern across all plugins:

1. **Explicit kwargs** (highest priority) - passed directly to `extract()`
2. **Environment variables** (fallback) - loaded from system environment
3. **Graceful failure** - plugins work without credentials when possible

This allows you to:
- Hard-code credentials for testing
- Use environment variables in production
- Share code without exposing credentials

## GoFile

### `password` (string, optional)

Password for accessing password-protected folders.

**Environment variable:** Not supported (passwords are folder-specific)

**Example:**

```python
import megaloader as mgl

# Public folder (no password needed)
for item in mgl.extract("https://gofile.io/d/abc123"):
    print(item.filename)

# Password-protected folder
for item in mgl.extract("https://gofile.io/d/xyz789", password="secret"):
    print(item.filename)
```

**CLI usage:**

```bash
# Public folder
megaloader download https://gofile.io/d/abc123 ./output

# Password-protected folder
megaloader download https://gofile.io/d/xyz789 ./output --password secret
```

**Notes:**
- GoFile hashes passwords using SHA-256 before sending to API
- Invalid passwords result in empty file lists
- No error is raised for incorrect passwords

## Fanbox

### `session_id` (string, required for most content)

Authentication cookie value for accessing creator content.

**Environment variable:** `FANBOX_SESSION_ID`

**How to obtain:**
1. Log in to Fanbox in your browser
2. Open browser DevTools (F12)
3. Go to Application/Storage → Cookies
4. Find cookie named `FANBOXSESSID`
5. Copy the value

**Example:**

```python
import megaloader as mgl

# Using explicit parameter
for item in mgl.extract(
    "https://creator.fanbox.cc",
    session_id="your_session_cookie_value"
):
    print(item.filename, item.collection_name)

# Using environment variable
import os
os.environ["FANBOX_SESSION_ID"] = "your_session_cookie_value"

for item in mgl.extract("https://creator.fanbox.cc"):
    print(item.filename)
```

**CLI usage:**

```bash
# Using environment variable
export FANBOX_SESSION_ID="your_session_cookie_value"
megaloader download https://creator.fanbox.cc ./output

# Or inline
FANBOX_SESSION_ID="your_session_cookie_value" megaloader download https://creator.fanbox.cc ./output
```

**Notes:**
- Most creator content requires authentication
- Session cookies expire periodically
- Without authentication, you'll get 403 Forbidden errors
- The plugin extracts profile assets, posts, images, and file attachments

## Pixiv

### `session_id` (string, required for most content)

Authentication cookie value for accessing artworks and user profiles.

**Environment variable:** `PIXIV_PHPSESSID`

**How to obtain:**
1. Log in to Pixiv in your browser
2. Open browser DevTools (F12)
3. Go to Application/Storage → Cookies
4. Find cookie named `PHPSESSID`
5. Copy the value

**Example:**

```python
import megaloader as mgl

# Single artwork
for item in mgl.extract(
    "https://www.pixiv.net/en/artworks/123456",
    session_id="your_session_cookie_value"
):
    print(item.filename)

# User profile (all works)
for item in mgl.extract(
    "https://www.pixiv.net/en/users/789012",
    session_id="your_session_cookie_value"
):
    print(item.filename, item.collection_name)
```

**CLI usage:**

```bash
# Using environment variable
export PIXIV_PHPSESSID="your_session_cookie_value"
megaloader download https://www.pixiv.net/en/artworks/123456 ./output

# Or inline
PIXIV_PHPSESSID="your_session_cookie_value" megaloader download https://www.pixiv.net/en/artworks/123456 ./output
```

**Notes:**
- Required for accessing most content
- Session cookies expire periodically
- Multi-page artworks are automatically detected
- User extraction includes profile images and all artworks

## Rule34

### `api_key` (string, optional)

API key for authenticated API access with higher rate limits.

**Environment variable:** `RULE34_API_KEY`

### `user_id` (string, optional)

User ID associated with the API key.

**Environment variable:** `RULE34_USER_ID`

**How to obtain:**
1. Create an account on Rule34
2. Go to account settings
3. Generate an API key
4. Note your user ID from your profile

**Example:**

```python
import megaloader as mgl

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

# Single post (no auth needed)
for item in mgl.extract("https://rule34.xxx/index.php?page=post&s=view&id=123456"):
    print(item.filename)
```

**CLI usage:**

```bash
# Using environment variables
export RULE34_API_KEY="your_api_key"
export RULE34_USER_ID="your_user_id"
megaloader download "https://rule34.xxx/index.php?page=post&s=list&tags=cat" ./output

# Or inline
RULE34_API_KEY="your_key" RULE34_USER_ID="your_id" megaloader download "https://rule34.xxx/..." ./output
```

**Notes:**
- API authentication is optional but recommended
- Without API credentials, the plugin falls back to web scraping (slower)
- API access provides better performance and reliability
- Rate limits are higher with authentication
- Both `api_key` and `user_id` must be provided together

## Credential precedence examples

Understanding how credentials are resolved:

```python
import os
import megaloader as mgl

# Scenario 1: Only environment variable
os.environ["FANBOX_SESSION_ID"] = "env_value"
for item in mgl.extract("https://creator.fanbox.cc"):
    pass  # Uses "env_value"

# Scenario 2: Both env var and kwarg (kwarg wins)
os.environ["FANBOX_SESSION_ID"] = "env_value"
for item in mgl.extract("https://creator.fanbox.cc", session_id="kwarg_value"):
    pass  # Uses "kwarg_value"

# Scenario 3: Neither provided
for item in mgl.extract("https://creator.fanbox.cc"):
    pass  # No authentication, may fail with 403
```

## Security best practices

::: danger Don't hard-Code credentials
Never commit credentials to version control or hard-code them in your application code.
:::

### Use environment variables

❌ **Bad:**
```python
for item in mgl.extract(url, session_id="abc123def456"):
    pass
```

✅ **Good:**
```python
import os
session_id = os.getenv("FANBOX_SESSION_ID")
for item in mgl.extract(url, session_id=session_id):
    pass
```

### Use environment variables

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

# Credentials are now available via os.getenv()
```

### Rotate credentials regularly

Session cookies and API keys can expire or be invalidated. Update them when:
- You get authentication errors
- Sessions expire (typically after weeks/months)
- You change your account password
