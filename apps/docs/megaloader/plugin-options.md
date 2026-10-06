# Plugin options

Some platforms take credentials or a password. Pass them as keyword arguments to
`extract()`:

```python
import megaloader as mgl

mgl.extract("https://gofile.io/d/abc123", password="secret")
```

Options a plugin does not use are ignored.

| Plugin   | Option       | Environment variable | Purpose                          |
| -------- | ------------ | -------------------- | -------------------------------- |
| `gofile` | `password`   |                      | Password of a protected folder.  |
| `gofile` | `token`      | `GOFILE_TOKEN`       | Account API token.               |
| `pixiv`  | `session_id` | `PIXIV_PHPSESSID`    | Value of the `PHPSESSID` cookie. |
| `rule34` | `api_key`    | `RULE34_API_KEY`     | API key.                         |
| `rule34` | `user_id`    | `RULE34_USER_ID`     | User ID that belongs to the key. |

An explicit argument wins over the environment variable. Megaloader reads
`os.environ` only. It does not load `.env` files, so load one yourself first if
you keep credentials in one.

## Command line

The CLI has `--password` and `--token` for GoFile. The other options are
reachable only through their environment variables:

```bash
export RULE34_API_KEY="your_api_key"
export RULE34_USER_ID="your_user_id"
megaloader download "https://rule34.xxx/index.php?page=post&s=list&tags=cat" cats
```

## GoFile

`token` is a Gofile account API token. Without one, the plugin creates a guest
account on the first request and reuses it for the rest of the process.

`password` unlocks a protected folder. The plugin sends its SHA-256 hash, not
the password. A folder that returns no files logs a warning and yields nothing.

The plugin signs each Gofile request with a salt. `GOFILE_SALT` overrides the
built-in value. It is read once, when `megaloader` is imported.

```python
for item in mgl.extract("https://gofile.io/d/abc123", token="your_api_token"):
    print(item.filename)
```

## Pixiv

`session_id` is the `PHPSESSID` cookie of a logged-in Pixiv session. The plugin
sends it as a cookie on `.pixiv.net` when set.

```python
for item in mgl.extract(
    "https://www.pixiv.net/en/users/789012", session_id="your_session_cookie"
):
    print(item.filename)
```

## Rule34

With `api_key` and `user_id` both set, the plugin queries the site's API for tag
URLs. With either one missing, it reads the listing pages instead. A single post
URL (with an `id` parameter) never uses the API.

```python
for item in mgl.extract(
    "https://rule34.xxx/index.php?page=post&s=list&tags=cat",
    api_key="your_api_key",
    user_id="your_user_id",
):
    print(item.filename)
```

## Credentials

Keep credentials out of source control. Read them from the environment:

```python
import os

session_id = os.environ["PIXIV_PHPSESSID"]
```
