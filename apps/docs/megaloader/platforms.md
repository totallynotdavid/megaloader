# Platforms

Megaloader has one plugin per platform family. `megaloader plugins` prints the
registered domains, and `megaloader.plugins.PLUGIN_REGISTRY` holds them in code.

| Plugin        | Domains                                        | URLs it reads                                      | Options              |
| ------------- | ---------------------------------------------- | -------------------------------------------------- | -------------------- |
| `bunkr`       | bunkr.ax, .black, .fi, .is, .la, .ru, .si, .su | `/a/<id>` album, `/f/<id>` file                    |                      |
| `cyberdrop`   | cyberdrop.cr, .me, .to                         | `/a/<id>` album, `/f/<id>` file                    |                      |
| `fapello`     | fapello.com                                    | `/<model>` profile                                 |                      |
| `gofile`      | gofile.io                                      | `/d/<id>` folder, `/f/<id>` file                   | `password`, `token`  |
| `pixeldrain`  | pixeldrain.com                                 | `/l/<id>` list, `/u/<id>` file                     |                      |
| `pixiv`       | pixiv.net and its subdomains                   | `/artworks/<id>`, `/users/<id>`, `member.php?id=`  | `session_id`         |
| `rule34`      | rule34.xxx                                     | a post or listing URL with an `id` or `tags` query | `api_key`, `user_id` |
| `thothub-to`  | thothub.ch, thothub.to                         | `/videos/`, `/albums/`, `/models/`                 |                      |
| `thothub-vip` | thothub.vip                                    | `/video/`, `/album/`, `/models/`                   |                      |
| `thotslife`   | thotslife.com                                  | a post URL                                         |                      |

[Plugin options](plugin-options) documents each option. A URL with a shape the
plugin does not read raises `ValueError`.

## What each plugin returns

**Bunkr.** Albums and single files. Every item carries
`Referer: https://get.bunkrr.su/`. Items from an album have no
`collection_name`.

**Cyberdrop.** Albums and single files. Album items take the album title as
`collection_name`.

**Fapello.** Every item on a model's profile, at full resolution.
`collection_name` is the model name.

**GoFile.** The files directly inside a folder, with the folder name as
`collection_name` and the size. Subfolders are skipped. Without a token the
plugin creates a guest account and reuses it for the rest of the process.

**PixelDrain.** A list or a single file, with `size_bytes`. The plugin reads the
page's embedded viewer data.

**Pixiv.** One artwork, or every artwork of a user. Multi-page artworks yield
one item per page, named `<id>_p<page>.<ext>`. A user URL also yields the
profile image as `avatar.<ext>` and the cover as `cover.<ext>` when the user has
them. Artwork items carry a `Referer` header.

**Rule34.** One post when the URL has `id`. Otherwise every post matching
`tags`, with the sorted tags joined by `_` as `collection_name`. With both
`api_key` and `user_id` the plugin uses the site's API. Without them it reads
the listing pages, 42 posts per page.

**Thothub.TO.** Videos, albums, and models. A model URL yields the model's
videos, with the model name as `collection_name`. Videos carry a `Referer`
header.

**Thothub.VIP.** Videos, albums, and models. A model URL yields the model's
videos, then its albums.

**Thotslife.** The videos and images in one post, with the post title as
`collection_name`.

## Add a platform

A new platform is a plugin class and an entry in the registries. See
[Writing plugins](writing-plugins).
