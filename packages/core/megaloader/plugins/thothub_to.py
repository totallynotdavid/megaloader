import logging
import os
import re
import tempfile
import time

from collections.abc import Generator
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests

from bs4 import BeautifulSoup

from megaloader.plugin import BasePlugin, Item


logger = logging.getLogger(__name__)


class ThothubTO(BasePlugin):
    """
    Extracts video and album URLs from Thothub[dot]to.

    For videos, the site hides the URL in 'flashvars' and uses obfuscated JS
    ('kt_player.js') to reveal them at runtime. This plugin mimics that logic.

    The deobfuscation process:
    1. Derive a 32-character key from 'license_code' in flashvars.
    2. Use the key to shuffle the first 32 chars of the URL hash.

    For albums, it parses the HTML to find direct (but redirected) image links.
    """

    # Regex to find video metadata from the flashvars object in the HTML
    _VIDEO_ID_RE = re.compile(r"video_id:\s*'(\d+)'")
    _LICENSE_CODE_RE = re.compile(r"license_code:\s*'(\$.+?)'")
    _VIDEO_URL_RE = re.compile(r"video_url:\s*'([^']+)'")
    _FILENAME_SANITIZE_RE = re.compile(r'[<>:"/\\|?*]')

    _OBFUSCATION_PREFIX = "function/0/"
    _FONT_SIZE_PX = 16
    _HASH_PREFIX_LENGTH = 32

    def __init__(self, url: str, **kwargs: Any) -> None:
        super().__init__(url, **kwargs)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
        )
        logger.debug("Initialized Thothub plugin with URL: %s", self.url)
        try:
            self.session.get("https://thothub.to/", timeout=30)
        except requests.RequestException:
            logger.warning(
                "Failed to pre-fetch homepage, session cookies might be incomplete.",
            )

    def _sanitize_filename(self, filename: str) -> str:
        return self._FILENAME_SANITIZE_RE.sub("_", filename).strip()

    def _generate_deobfuscation_key(self, license_code: str) -> str:
        """
        Generates the 32-digit deobfuscation key from the license_code,
        replicating obfuscated logic from kt_player.js.

        JS logic overview:
        1. From license_code, build `f` by converting digits; '0' and non-digits to '1'.
        2. Compute `f2` from the difference of halves of `f`, doubled.
        3. Use nested loop to generate key `m` using digits from license_code and `f2`.

        Snippet from kt_player.js:
        ```
        function(a, b, c) { // a=conf, b=license_code_key, c=license_code_val
            ...
            if (d) { // d is the license_code
                for (f = "", g = 1; g < d.length; g++)
                    // The ternary here is tricky: parseInt('0') is falsy in JS, so it returns 1.
                    f += o(d[g]) ? o(d[g]) : 1;
                for (j = o(f.length / 2),
                k = o(f.substring(0, j + 1)),
                l = o(f.substring(j)),
                ...
                f = "" + f,
                i = o(c) / 2 + 2, // c is '16px', so o(c) is 16. i becomes 10.
                m = "",
                g = 0; g < j + 1; g++)
                    for (h = 1; h <= 4; h++)
                        n = o(d[g + h]) + o(f[g]), // f is the recalculated f_str_2
                        n >= i && (n -= i),
                        m += n;
                return m // This is the final 32-digit key
            }
        }
        ```
        """
        # Corresponds to JS `f += o(d[g]) ? o(d[g]) : 1;`
        f_str = ""
        for char in license_code[1:]:  # JS loop starts at g=1
            if char.isdigit():
                digit = int(char)
                # In JS, parseInt('0') is 0, which is falsy, making the
                # ternary expression return 1
                f_str += str(digit) if digit != 0 else "1"
            else:
                f_str += "1"

        # Corresponds to JS vars `j`, `k`, `l`, and the recalculation of `f`
        j = len(f_str) // 2
        k = int(f_str[: j + 1])
        l_val = int(f_str[j:])
        f_val = abs(l_val - k) + abs(k - l_val)
        f_val *= 2
        f_str_2 = str(f_val)

        # Corresponds to JS `i = o(c) / 2 + 2`, where `c` is '16px'
        i_val = self._FONT_SIZE_PX // 2 + 2
        final_key = ""
        # Corresponds to the final nested loop that builds the key `m`
        for g in range(j + 1):
            for h in range(1, 5):
                try:
                    d_digit = int(license_code[g + h])
                except (ValueError, IndexError):
                    d_digit = 0

                # Use modulo to wrap around f_str_2 if g is too large
                f_digit = int(f_str_2[g % len(f_str_2)])
                n = d_digit + f_digit

                if n >= i_val:
                    n -= i_val
                final_key += str(n)
        return final_key

    def _deobfuscate_hash(self, hash_to_decode: str, key: str) -> str:
        """
        Shuffles the first 32 characters of the hash using the given key.

        Replicates kt_player.js logic:
        For each position k (from end to start), sum digits of key[k:]
        to compute l, then swap chars at k and l.

        Snippet from kt_player.js:
        ```
        function(a, b, c, d, e) { // b=key, c=hash, d='16px'
            ...
            var h = g[6].substring(0, 2 * parseInt(d)) // The hash to be shuffled (first 32 chars)
            var i = e ? e(a, c, d) : ""; // The generated key
            ...
            for (var j = h, k = h.length - 1; k >= 0; k--) {
                for (var l = k, m = k; m < i.length; m++)
                    l += parseInt(i[m]); // Sums digits of the key from index k onwards
                for (; l >= h.length; )
                    l -= h.length;
                // Swaps character at k with character at new position l
                for (var n = "", o = 0; o < h.length; o++)
                    n += o == k ? h[l] : o == l ? h[k] : h[o];
                h = n
            }
            g[6] = g[6].replace(j, h) // Replaces the original hash part with the shuffled one
        }
        ```
        """
        h_list = list(hash_to_decode)
        h_len = len(h_list)

        # Traverse backwards through the hash
        # Corresponds to: `for (var k = h.length - 1; k >= 0; k--)`
        for k in range(h_len - 1, -1, -1):
            l_val = k
            # Sum digits of key starting from index k
            # Corresponds to: `for (var m = k; m < i.length; m++) l += parseInt(i[m]);`
            key_subset_sum = sum(int(digit) for digit in key[k:])
            l_val += key_subset_sum

            # Corresponds to `for (; l >= h.length; ) l -= h.length;`
            l_val %= h_len  # Wrap if out of bounds

            # Swap positions k and l_val
            h_list[k], h_list[l_val] = h_list[l_val], h_list[k]

        return "".join(h_list)

    def _get_item_from_video_page(
        self,
        page_url: str,
        album_title: str | None = None,
    ) -> Item | None:
        content: str = ""
        try:
            # First: Get the video page content. All necessary data is here.
            logger.debug("Fetching video page to get metadata: %s", page_url)
            page_response = self.session.get(page_url, timeout=30)
            page_response.raise_for_status()
            content = page_response.text

            # Second: Extract the required pieces from the 'flashvars' object.
            video_id_match = self._VIDEO_ID_RE.search(content)
            obfuscated_url_match = self._VIDEO_URL_RE.search(content)
            license_code_match = self._LICENSE_CODE_RE.search(content)

            if not video_id_match or not obfuscated_url_match or not license_code_match:
                logger.error(
                    "Could not find video_id, video_url, or license_code on page %s. The video might not be public.",
                    page_url,
                )
                return None

            video_id = video_id_match.group(1)
            obfuscated_url = obfuscated_url_match.group(1).replace(
                self._OBFUSCATION_PREFIX,
                "",
            )
            license_code = license_code_match.group(1)

            # Third: Replicate the deobfuscation process.
            # a. Generate the 32-digit key from the license code.
            deobfuscation_key = self._generate_deobfuscation_key(license_code)

            # b. Isolate the hash from the URL. It's the 6th component (index 5).
            url_parts = obfuscated_url.split("/")
            original_hash = url_parts[5]

            # c. IMPORTANT: The shuffling logic only applies to the first 32 characters.
            hash_to_shuffle = original_hash[: self._HASH_PREFIX_LENGTH]
            rest_of_hash = original_hash[self._HASH_PREFIX_LENGTH :]

            # d. Shuffle the 32-character prefix using the generated key.
            shuffled_prefix = self._deobfuscate_hash(hash_to_shuffle, deobfuscation_key)

            # e. Recombine the shuffled prefix and the rest of the hash.
            deobfuscated_hash = shuffled_prefix + rest_of_hash
            url_parts[5] = deobfuscated_hash

            # Finally: Reconstruct the final URL.
            base_video_url = "/".join(url_parts)
            rnd_timestamp = int(time.time() * 1000)
            separator = "&" if "?" in base_video_url else "?"
            final_video_url = f"{base_video_url}{separator}rnd={rnd_timestamp}"

            soup = BeautifulSoup(content, "html.parser")
            title_tag = soup.find("h1")
            title = title_tag.text.strip() if title_tag else f"thothub_{video_id}"
            sanitized_title = self._sanitize_filename(title)

            logger.info("Successfully retrieved real video URL for '%s'", title)
            logger.debug("Final URL: %s", final_video_url)
            return Item(
                url=final_video_url,
                filename=f"{sanitized_title}.mp4",
                album_title=album_title,
                metadata={"referer": page_url},
            )
        except requests.RequestException:
            logger.exception("Failed to process video page %s", page_url)
            return None
        except Exception:
            logger.exception(
                "An unexpected error occurred while processing %s",
                page_url,
            )
            try:
                debug_fd, debug_path = tempfile.mkstemp(
                    prefix="thothub_debug_",
                    suffix=".html",
                )
                with os.fdopen(debug_fd, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info("Saved the page content to: %s", debug_path)
            except OSError as debug_err:
                logger.warning("Failed to write debug file: %s", debug_err)
            return None

    def export(self) -> Generator[Item, None, None]:
        parsed_url = urlparse(self.url)
        path = parsed_url.path
        if path.startswith("/videos/"):
            item = self._get_item_from_video_page(self.url)
            if item:
                yield item
        elif path.startswith("/models/"):
            yield from self._export_from_model_page()
        elif path.startswith("/albums/"):
            yield from self._export_from_album_page()
        else:
            logger.error("Unrecognized Thothub URL format: %s", self.url)

    def _export_from_album_page(self) -> Generator[Item, None, None]:
        logger.info("Exporting all images from album: %s", self.url)
        try:
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
            content = response.text
            soup = BeautifulSoup(content, "html.parser")

            album_title_tag = soup.find("h1")
            album_title = (
                album_title_tag.text.strip() if album_title_tag else "thothub_album"
            )
            sanitized_album_title = self._sanitize_filename(album_title)

            image_links = soup.select('div.block-album a.item[href*="/get_image/"]')
            if not image_links:
                logger.warning("No image links found on album page: %s", self.url)
                return

            logger.info("Found %d images in album '%s'.", len(image_links), album_title)

            for i, a_tag in enumerate(image_links):
                image_page_url = a_tag.get("href")
                if not image_page_url:
                    continue

                full_image_url = urljoin(self.url, str(image_page_url))
                # The URL path is like: /get_image/.../sources/.../XXXXXXX.jpg/
                # We extract 'XXXXXXX.jpg' as the filename.
                path_part = urlparse(full_image_url).path.strip("/")
                filename = Path(path_part).name

                if not filename:
                    ext_match = re.search(r"\.(\w+)$", path_part)
                    ext = ext_match.group(1) if ext_match else "jpg"
                    filename = f"image_{i + 1}.{ext}"

                yield Item(
                    url=full_image_url,
                    filename=filename,
                    album_title=sanitized_album_title,
                    metadata={"referer": self.url},
                )
        except requests.RequestException:
            logger.exception("Failed to fetch album page %s", self.url)
        except Exception:
            logger.exception(
                "An unexpected error occurred while processing album %s",
                self.url,
            )

    def _export_from_model_page(self) -> Generator[Item, None, None]:
        model_match = re.search(r"/models/([^/]+)", self.url)

        if not model_match:
            logger.error("Could not extract model name from URL: %s", self.url)
            return

        model_name = model_match.group(1)
        logger.info("Exporting all videos for model: %s", model_name)

        page_num = 1
        seen_urls = set()
        while True:
            ajax_url = (
                f"https://thothub.to/models/{model_name}/?mode=async&function=get_block"
                f"&block_id=list_videos_common_videos_list&sort_by=post_date&from={page_num}"
            )
            try:
                logger.debug("Fetching AJAX page %d for %s", page_num, model_name)
                response = self.session.get(ajax_url, timeout=30)
                if response.status_code == 404:
                    logger.info("Reached the end of model's videos (404).")
                    break
                response.raise_for_status()
            except requests.RequestException:
                logger.exception("Failed to fetch AJAX page %d", page_num)
                break

            html_snippet = response.text
            if not html_snippet.strip():
                logger.info("Reached the end of model's videos (empty page).")
                break

            soup = BeautifulSoup(html_snippet, "html.parser")
            video_links = [
                a["href"] for a in soup.select('div.item > a[href*="/videos/"]')
            ]

            if not video_links:
                logger.info("No more video links found on this page.")
                break

            sanitized_model_name = self._sanitize_filename(model_name)

            for link in video_links:
                video_page_url = urljoin("https://thothub.to/", str(link))

                if video_page_url in seen_urls:
                    continue

                seen_urls.add(video_page_url)
                item = self._get_item_from_video_page(
                    video_page_url,
                    album_title=sanitized_model_name,
                )

                if item:
                    yield item
            page_num += 1

    def download_file(self, item: Item, output_dir: str) -> bool:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        final_output_dir = Path(output_dir)

        if item.album_title:
            sanitized_album_title = self._sanitize_filename(item.album_title)

            if Path(output_dir).name != sanitized_album_title:
                final_output_dir = Path(output_dir) / sanitized_album_title
                Path(final_output_dir).mkdir(parents=True, exist_ok=True)

        output_path = Path(final_output_dir) / item.filename
        if output_path.exists():
            logger.info("File already exists: %s", item.filename)
            return True

        referer = item.metadata.get("referer") if item.metadata else None
        if not referer:
            logger.error("Cannot download %s, missing referer URL.", item.filename)
            return False

        headers = dict(self.session.headers)
        headers["Referer"] = referer
        headers["Range"] = "bytes=0-"
        try:
            logger.debug(
                "Downloading: %s to %s with headers: %s",
                item.url,
                output_path,
                headers,
            )
            with self.session.get(
                item.url,
                headers=headers,
                stream=True,
                timeout=3600,
                allow_redirects=True,
            ) as response:
                response.raise_for_status()
                with Path(output_path).open("wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            logger.info("Downloaded: %s", item.filename)
        except requests.RequestException:
            logger.exception("Download failed for %s", item.filename)
            if output_path.exists():
                output_path.unlink()
            return False
        else:
            return True
