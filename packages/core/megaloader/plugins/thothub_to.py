import logging
import re
import time

from collections.abc import Generator
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)


class ThothubTO(BasePlugin):
    """Extract content from Thothub.to."""

    def extract(self) -> Generator[DownloadItem, None, None]:
        path = urlparse(self.url).path

        if path.startswith("/videos/"):
            if item := self._extract_video(self.url):
                yield item
        elif path.startswith("/models/"):
            yield from self._extract_model()
        elif path.startswith("/albums/"):
            yield from self._extract_album()
        else:
            logger.warning("Unrecognized Thothub URL format")

    def _extract_video(
        self, url: str, collection_name: str | None = None
    ) -> DownloadItem | None:
        """Extract video from page."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            content = response.text

            # Extract flashvars
            video_id = re.search(r"video_id:\s*'(\d+)'", content)
            video_url = re.search(r"video_url:\s*'([^']+)'", content)
            license_code = re.search(r"license_code:\s*'(\$.+?)'", content)

            if not (video_id and video_url and license_code):
                return None

            # Deobfuscate URL
            obfuscated = video_url.group(1).replace("function/0/", "")
            key = self._generate_key(license_code.group(1))
            parts = obfuscated.split("/")
            parts[5] = self._deobfuscate_hash(parts[5], key)

            final_url = "/".join(parts) + f"?rnd={int(time.time() * 1000)}"

            # Extract title
            soup = BeautifulSoup(content, "html.parser")
            h1 = soup.find("h1")
            title = h1.text.strip() if h1 else f"video_{video_id.group(1)}"

            return DownloadItem(
                download_url=final_url,
                filename=f"{title}.mp4",
                collection_name=collection_name,
                headers={"Referer": url},
            )
        except Exception:
            logger.debug("Video extraction failed", exc_info=True)
            return None

    def _extract_album(self) -> Generator[DownloadItem, None, None]:
        """Extract images from album."""
        response = self.session.get(self.url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        h1 = soup.find("h1")
        collection_name = h1.text.strip() if h1 else "album"

        for link in soup.select('div.block-album a.item[href*="/get_image/"]'):
            if href := link.get("href"):
                full_url = urljoin(self.url, str(href))
                filename = Path(urlparse(full_url).path.strip("/")).name

                yield DownloadItem(
                    download_url=full_url,
                    filename=filename,
                    collection_name=collection_name,
                )

    def _extract_model(self) -> Generator[DownloadItem, None, None]:
        """Extract all videos from model page."""
        model_name = urlparse(self.url).path.split("/")[2]
        page = 1
        seen = set()

        while True:
            url = f"https://thothub.to/models/{model_name}/?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from={page}"

            response = self.session.get(url)
            if response.status_code == 404 or not response.text.strip():
                break

            soup = BeautifulSoup(response.text, "html.parser")
            links = [
                str(link["href"])
                for link in soup.select('div.item > a[href*="/videos/"]')
                if link.get("href")
            ]

            if not links:
                break

            for link in links:
                full_url = urljoin("https://thothub.to/", link)
                if full_url in seen:
                    continue

                seen.add(full_url)
                if item := self._extract_video(full_url, model_name):
                    yield item

            page += 1

    def _generate_key(self, code: str) -> str:
        """Generate deobfuscation key."""
        f_str = "".join(
            str(int(c)) if c.isdigit() and int(c) != 0 else "1" for c in code[1:]
        )
        j = len(f_str) // 2
        k = int(f_str[: j + 1])
        length = int(f_str[j:])
        f2 = str((abs(length - k) + abs(k - length)) * 2)

        key = ""
        for g in range(j + 1):
            for h in range(1, 5):
                try:
                    d = int(code[g + h])
                except (IndexError, ValueError):
                    d = 0
                n = d + int(f2[g % len(f2)])
                if n >= 10:
                    n -= 10
                key += str(n)

        return key

    def _deobfuscate_hash(self, h: str, key: str) -> str:
        """Deobfuscate video hash."""
        hl = list(h)
        prefix = hl[:32]
        suffix = hl[32:]

        for k in range(len(prefix) - 1, -1, -1):
            swap_idx = (k + sum(int(d) for d in key[k:])) % len(prefix)
            prefix[k], prefix[swap_idx] = prefix[swap_idx], prefix[k]

        return "".join(prefix + suffix)
