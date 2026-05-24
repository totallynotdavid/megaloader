import logging
import re
import time

from collections.abc import Generator
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from megaloader.exceptions import ExtractionError
from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)


class ThothubTO(BasePlugin):
    """Extract content from Thothub.to."""

    def extract(self) -> Generator[DownloadItem, None, None]:
        path = urlparse(self.url).path

        if path.startswith("/videos/"):
            yield self._extract_video(self.url)
        elif path.startswith("/models/"):
            yield from self._extract_model()
        elif path.startswith("/albums/"):
            yield from self._extract_album()
        else:
            logger.warning("Unrecognized Thothub URL format")

    def _extract_video(
        self, url: str, collection_name: str | None = None
    ) -> DownloadItem:
        response = self._get(url)
        content = response.text

        video_id = re.search(r"video_id:\s*'(\d+)'", content)
        video_url = re.search(r"video_url:\s*'([^']+)'", content)
        license_code = re.search(r"license_code:\s*'(\$.+?)'", content)

        if not (video_id and video_url and license_code):
            from megaloader.error_policy import raise_extraction_error

            raise_extraction_error(
                f"Could not extract video metadata: {url}",
                source="thothubto",
                url=url,
                category="protocol",
            )

        obfuscated = video_url.group(1).replace("function/0/", "")
        key = self._generate_key(license_code.group(1))
        parts = obfuscated.split("/")
        parts[5] = self._deobfuscate_hash(parts[5], key)

        final_url = "/".join(parts) + f"?rnd={int(time.time() * 1000)}"

        soup = BeautifulSoup(content, "html.parser")
        h1 = soup.find("h1")
        title = h1.text.strip() if h1 else f"video_{video_id.group(1)}"

        return DownloadItem(
            download_url=final_url,
            filename=f"{title}.mp4",
            collection_name=collection_name,
            headers={"Referer": url},
        )

    def _extract_album(self) -> Generator[DownloadItem, None, None]:
        response = self._get(self.url)
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
        parsed = urlparse(self.url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        model_name = parsed.path.split("/")[2]
        page = 1
        seen: set[str] = set()

        while True:
            pagination_url = (
                f"{base_url}/models/{model_name}/"
                f"?mode=async&function=get_block&block_id=list_videos_common_videos_list"
                f"&sort_by=post_date&from={page}"
            )

            try:
                response = self._get(pagination_url)
            except ExtractionError as e:
                if e.http_status == 404:
                    break
                raise

            if not response.text.strip():
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
                full_url = urljoin(base_url, link)
                if full_url in seen:
                    continue

                seen.add(full_url)
                yield self._extract_video(full_url, model_name)

            page += 1

    def _generate_key(self, code: str) -> str:
        """Deobfuscation key derivation from license_code (site-specific algorithm)."""
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
        """Hash deobfuscation to reconstruct the CDN path segment."""
        hl = list(h)
        prefix = hl[:32]
        suffix = hl[32:]

        for k in range(len(prefix) - 1, -1, -1):
            swap_idx = (k + sum(int(d) for d in key[k:])) % len(prefix)
            prefix[k], prefix[swap_idx] = prefix[swap_idx], prefix[k]

        return "".join(prefix + suffix)
