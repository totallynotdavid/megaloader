import logging
import re
import time

from collections.abc import Generator
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from megaloader.plugin import BasePlugin, Item


logger = logging.getLogger(__name__)


class ThothubTO(BasePlugin):
    def extract(self) -> Generator[Item, None, None]:
        path = urlparse(self.url).path
        if path.startswith("/videos/"):
            if item := self._process_video_page(self.url):
                yield item
        elif path.startswith("/models/"):
            yield from self._process_model()
        elif path.startswith("/albums/"):
            yield from self._process_album()
        else:
            logger.warning("Unrecognized Thothub URL")

    def _process_video_page(
        self, url: str, album_title: str | None = None
    ) -> Item | None:
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            content = resp.text

            # Extract flashvars
            vid = re.search(r"video_id:\s*'(\d+)'", content)
            vurl = re.search(r"video_url:\s*'([^']+)'", content)
            code = re.search(r"license_code:\s*'(\$.+?)'", content)

            if not (vid and vurl and code):
                return None

            # Deobfuscate
            obfuscated = vurl.group(1).replace("function/0/", "")
            key = self._generate_key(code.group(1))
            parts = obfuscated.split("/")
            parts[5] = self._deobfuscate_hash(parts[5], key)

            final_url = "/".join(parts) + f"?rnd={int(time.time() * 1000)}"

            soup = BeautifulSoup(content, "html.parser")
            title = (
                soup.find("h1").text.strip()
                if soup.find("h1")
                else f"video_{vid.group(1)}"
            )

            return Item(
                url=final_url,
                filename=f"{self._sanitize(title)}.mp4",
                album=album_title,
                meta={"referer": url},
            )
        except Exception:
            logger.exception("Video extraction failed")
            return None

    def _process_album(self) -> Generator[Item, None, None]:
        resp = self.session.get(self.url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        title = soup.find("h1").text.strip() if soup.find("h1") else "album"
        album_title = self._sanitize(title)

        for link in soup.select('div.block-album a.item[href*="/get_image/"]'):
            full_url = urljoin(self.url, link.get("href"))
            fname = Path(urlparse(full_url).path.strip("/")).name
            yield Item(url=full_url, filename=fname, album=album_title)

    def _process_model(self) -> Generator[Item, None, None]:
        model = urlparse(self.url).path.split("/")[2]
        page = 1
        seen = set()

        while True:
            url = f"https://thothub.to/models/{model}/?mode=async&function=get_block&block_id=list_videos_common_videos_list&sort_by=post_date&from={page}"
            resp = self.session.get(url)
            if resp.status_code == 404 or not resp.text.strip():
                break

            links = [
                link["href"]
                for link in BeautifulSoup(resp.text, "html.parser").select(
                    'div.item > a[href*="/videos/"]'
                )
            ]
            if not links:
                break

            for link in links:
                full = urljoin("https://thothub.to/", link)
                if full in seen:
                    continue
                seen.add(full)
                if item := self._process_video_page(full, self._sanitize(model)):
                    yield item
            page += 1

    def _sanitize(self, name: str) -> str:
        return re.sub(r'[<>:"/\\|?*]', "_", name).strip()

    def _generate_key(self, code: str) -> str:
        f_str = "".join(
            [str(int(c)) if c.isdigit() and int(c) != 0 else "1" for c in code[1:]]
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
        hl = list(h)
        prefix = hl[:32]
        suffix = hl[32:]
        # Shuffle logic on prefix
        for k in range(len(prefix) - 1, -1, -1):
            swap_idx = (k + sum(int(d) for d in key[k:])) % len(prefix)
            prefix[k], prefix[swap_idx] = prefix[swap_idx], prefix[k]
        return "".join(prefix + suffix)
