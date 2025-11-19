"""
Test URLs for live site monitoring.

These URLs should be:
1. Publicly accessible (no auth required unless marked)
2. Relatively stable (won't be deleted soon)
3. Small/fast to process (for quick CI runs)

Update these if test albums get deleted or rate-limited.
"""

BUNKR_URLS = {
    "images": "https://bunkr.si/a/xYKtNmBx",
    "videos": "https://bunkr.si/a/I4TiEKcm",
    "single_file": "https://bunkr.si/f/z0EW9Wc6zxhA7",  # first item from the first album (images)
}

CYBERDROP_URLS = {
    "images": "https://cyberdrop.me/a/w4iUzGgx",
    "videos": "https://cyberdrop.me/a/9ZwBUxsC",
    "single_file": "https://cyberdrop.me/f/7rw3VENyC62mB",  # first item from first album (images)
}

GOFILE_URLS = {
    "images": "https://gofile.io/d/wUbPe1",
    "videos": "https://gofile.io/d/8ZQdNo",
}

PIXELDRAIN_URLS = {
    "images": "https://pixeldrain.com/l/DDGtvvTU",
    "videos": "https://pixeldrain.com/l/zqoz6uFE",
    "single_file": "https://pixeldrain.com/u/WnQte6cf",  # first item from the images album
}

FAPELLO_URLS = {
    "model": "https://fapello.com/narabask/",
}

PIXIV_URLS = {
    "artwork": "https://www.pixiv.net/en/artworks/51400046",
}
