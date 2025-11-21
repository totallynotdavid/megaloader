# Supported Platforms

Megaloader supports 11 file hosting and media platforms through dedicated plugins. Platforms are divided into two tiers based on maintenance priority.

## Platform Tiers

### Core Platforms

Core platforms receive active development, testing, and maintenance. These are the primary focus of the project:

- **Bunkr** - File hosting with album support
- **Cyberdrop** - File hosting and galleries
- **GoFile** - File hosting with password protection
- **PixelDrain** - File hosting with lists and single files

### Extended Platforms

Extended platforms are supported on a best-effort basis. They may have limitations or require additional configuration:

- **Fanbox** - Creator content platform (requires authentication)
- **Fapello** - Media galleries
- **Pixiv** - Art and illustration platform (requires authentication)
- **Rule34** - Image board (supports API authentication)
- **ThotsLife** - Media galleries
- **ThotHub.TO** - Media galleries
- **ThotHub.VIP** - Media galleries

## Platform Details

### Bunkr

**Supported Domains:**
- `bunkr.si`
- `bunkr.la`
- `bunkr.is`
- `bunkr.ru`
- `bunkr.su`

**Features:**
- Album extraction
- Individual file downloads
- Automatic collection naming

**Known Limitations:**
- None

**Example:**
```python
import megaloader as mgl

for item in mgl.extract("https://bunkr.si/a/album123"):
    print(item.filename, item.collection_name)
```

---

### Cyberdrop

**Supported Domains:**
- `cyberdrop.cr`
- `cyberdrop.me`
- `cyberdrop.to`

**Features:**
- Album extraction
- Gallery support
- Collection organization

**Known Limitations:**
- None

**Example:**
```python
for item in mgl.extract("https://cyberdrop.me/a/gallery456"):
    print(item.filename)
```

---

### GoFile

**Supported Domains:**
- `gofile.io`

**Features:**
- Folder extraction
- Password-protected content support
- Automatic guest account creation

**Known Limitations:**
- Requires password for protected folders

**Example:**
```python
# Public folder
for item in mgl.extract("https://gofile.io/d/abc123"):
    print(item.filename)

# Password-protected folder
for item in mgl.extract("https://gofile.io/d/xyz789", password="secret"):
    print(item.filename)
```

---

### PixelDrain

**Supported Domains:**
- `pixeldrain.com`

**Features:**
- List extraction
- Single file support
- File size metadata

**Known Limitations:**
- None

**Example:**
```python
# List of files
for item in mgl.extract("https://pixeldrain.com/l/list123"):
    print(item.filename, item.size_bytes)

# Single file
for item in mgl.extract("https://pixeldrain.com/u/file456"):
    print(item.filename)
```

---

### Fanbox

**Supported Domains:**
- `fanbox.cc` (including creator subdomains like `creator.fanbox.cc`)

**Features:**
- Creator profile extraction
- Post content extraction
- Image and file attachment support
- Profile assets (avatar, banner)

**Known Limitations:**
- Requires authentication for most content
- Some posts may be subscriber-only

**Authentication Required:**
Yes - requires `session_id` parameter or `FANBOX_SESSION_ID` environment variable

**Example:**
```python
for item in mgl.extract(
    "https://creator.fanbox.cc",
    session_id="your_session_cookie"
):
    print(item.filename, item.collection_name)
```

---

### Fapello

**Supported Domains:**
- `fapello.com`

**Features:**
- Model gallery extraction
- Image and video support

**Known Limitations:**
- May have rate limiting

**Example:**
```python
for item in mgl.extract("https://fapello.com/model-name/"):
    print(item.filename)
```

---

### Pixiv

**Supported Domains:**
- `pixiv.net` (including subdomains)

**Features:**
- Artwork extraction
- User gallery support
- Multiple image posts

**Known Limitations:**
- Requires authentication for most content
- Rate limiting may apply

**Authentication Required:**
Yes - requires `session_id` parameter or `PIXIV_SESSION_ID` environment variable

**Example:**
```python
for item in mgl.extract(
    "https://www.pixiv.net/en/artworks/123456",
    session_id="your_session_cookie"
):
    print(item.filename)
```

---

### Rule34

**Supported Domains:**
- `rule34.xxx`

**Features:**
- Post extraction
- Tag-based searches
- API support

**Known Limitations:**
- API rate limits apply
- Some content may require authentication

**Authentication Optional:**
API key and user ID can be provided for higher rate limits

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

---

### ThotsLife

**Supported Domains:**
- `thotslife.com`

**Features:**
- Model gallery extraction
- Image and video support

**Known Limitations:**
- May have rate limiting

**Example:**
```python
for item in mgl.extract("https://thotslife.com/model-name"):
    print(item.filename)
```

---

### ThotHub.TO

**Supported Domains:**
- `thothub.ch`
- `thothub.to`

**Features:**
- Model gallery extraction
- Image and video support

**Known Limitations:**
- May have rate limiting

**Example:**
```python
for item in mgl.extract("https://thothub.to/model-name/"):
    print(item.filename)
```

---

### ThotHub.VIP

**Supported Domains:**
- `thothub.vip`

**Features:**
- Model gallery extraction
- Image and video support

**Known Limitations:**
- May have rate limiting

**Example:**
```python
for item in mgl.extract("https://thothub.vip/model-name/"):
    print(item.filename)
```

## Checking Supported Platforms

You can list all supported platforms using the CLI:

```bash
megaloader plugins
```

Or programmatically:

```python
from megaloader.plugins import PLUGIN_REGISTRY

for domain in sorted(PLUGIN_REGISTRY.keys()):
    print(domain)
```

## Requesting New Platforms

To request support for a new platform, please open an issue on the GitHub repository with:

- Platform URL and domain
- Example URLs showing different content types
- Any authentication requirements
- API documentation (if available)

## Next Steps

- [Plugin Options](./plugin-options.md) - Learn about platform-specific parameters
- [Creating Plugins](./creating-plugins.md) - Build support for new platforms
