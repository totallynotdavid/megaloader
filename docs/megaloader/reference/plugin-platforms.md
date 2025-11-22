# Supported platforms

Megaloader supports 11 file hosting platforms through dedicated plugins.
Platforms are split into core (actively maintained) and extended (best-effort
support) tiers.

## Core platforms

These receive active development and testing:

### Bunkr

File hosting with album support across multiple domains.

**Domains:** bunkr.si, bunkr.la, bunkr.is, bunkr.ru, bunkr.su

**Features:** Album extraction, individual files, automatic collection naming

**Example:**

```python
for item in mgl.extract("https://bunkr.si/a/album123"):
    print(item.filename, item.collection_name)
```

### Cyberdrop

File hosting and galleries.

**Domains:** cyberdrop.cr, cyberdrop.me, cyberdrop.to

**Features:** Album extraction, gallery support, collection organization

**Example:**

```python
for item in mgl.extract("https://cyberdrop.me/a/gallery456"):
    print(item.filename)
```

### GoFile

File hosting with password protection.

**Domains:** gofile.io

**Features:** Folder extraction, password-protected content, automatic guest
accounts

**Requires:** Password for protected folders

**Example:**

```python
# Public folder
for item in mgl.extract("https://gofile.io/d/abc123"):
    print(item.filename)

# Password-protected
for item in mgl.extract("https://gofile.io/d/xyz789", password="secret"):
    print(item.filename)
```

### PixelDrain

File hosting with lists and single files.

**Domains:** pixeldrain.com

**Features:** List extraction, single file support, file size metadata

**Example:**

```python
# List
for item in mgl.extract("https://pixeldrain.com/l/list123"):
    print(item.filename, item.size_bytes)

# Single file
for item in mgl.extract("https://pixeldrain.com/u/file456"):
    print(item.filename)
```

## Extended platforms

Best-effort support with possible limitations:

### Fanbox

Creator content platform requiring authentication.

**Domains:** fanbox.cc (including creator subdomains)

**Features:** Creator profiles, post content, images, file attachments, profile
assets

**Requires:** `session_id` parameter or `FANBOX_SESSION_ID` environment variable

**Example:**

```python
for item in mgl.extract(
    "https://creator.fanbox.cc",
    session_id="your_session_cookie"
):
    print(item.filename, item.collection_name)
```

### Fapello

Media galleries.

**Domains:** fapello.com

**Features:** Model gallery extraction, images and videos

**Example:**

```python
for item in mgl.extract("https://fapello.com/model-name/"):
    print(item.filename)
```

### Pixiv

Art and illustration platform requiring authentication.

**Domains:** pixiv.net (including subdomains)

**Features:** Artwork extraction, user galleries, multiple image posts

**Requires:** `session_id` parameter or `PIXIV_SESSION_ID` environment variable

**Example:**

```python
for item in mgl.extract(
    "https://www.pixiv.net/en/artworks/123456",
    session_id="your_session_cookie"
):
    print(item.filename)
```

### Rule34

Image board with optional API authentication.

**Domains:** rule34.xxx

**Features:** Post extraction, tag-based searches, API support

**Authentication:** Optional `api_key` and `user_id` for higher rate limits

**Example:**

```python
# Without authentication
for item in mgl.extract("https://rule34.xxx/index.php?page=post&s=view&id=123"):
    print(item.filename)

# With API authentication
for item in mgl.extract(
    "https://rule34.xxx/index.php?page=post&s=view&id=123",
    api_key="your_key",
    user_id="your_id"
):
    print(item.filename)
```

### ThotsLife

Media galleries.

**Domains:** thotslife.com

**Features:** Model gallery extraction, images and videos

**Example:**

```python
for item in mgl.extract("https://thotslife.com/model-name"):
    print(item.filename)
```

### ThotHub.TO

Media galleries.

**Domains:** thothub.ch, thothub.to

**Features:** Model gallery extraction, images and videos

**Example:**

```python
for item in mgl.extract("https://thothub.to/model-name/"):
    print(item.filename)
```

### ThotHub.VIP

Media galleries.

**Domains:** thothub.vip

**Features:** Model gallery extraction, images and videos

**Example:**

```python
for item in mgl.extract("https://thothub.vip/model-name/"):
    print(item.filename)
```

## Checking platform support

List all supported platforms with the CLI:

```bash
megaloader plugins
```

Or programmatically:

```python
from megaloader.plugins import PLUGIN_REGISTRY

for domain in sorted(PLUGIN_REGISTRY.keys()):
    print(domain)
```

Check if a specific domain is supported:

```python
from megaloader.plugins import get_plugin_class

if get_plugin_class("pixeldrain.com"):
    print("Supported")
```

## Requesting new platforms

To request support for a new platform, open a discussion on GitHub with:

- Platform URL and domain
- Example URLs showing different content types
- Authentication requirements
- API documentation (if available)
