import requests
import re
import os
import json
import math
from urllib.parse import urlparse
from typing import Generator, Tuple, Optional
from ..plugin import BasePlugin


class PixelDrain(BasePlugin):
    # Provided by https://github.com/sh13y/pixeldrain-ratelimit-bypasser
    PROXIES = [
        "pd1.sriflix.my",
        "pd2.sriflix.my",
        "pd3.sriflix.my",
        "pd4.sriflix.my",
        "pd5.sriflix.my",
        "pd6.sriflix.my",
        "pd7.sriflix.my",
        "pd8.sriflix.my",
        "pd9.sriflix.my",
        "pd10.sriflix.my",
    ]

    def __init__(self, url: str):
        super().__init__(url)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        self.proxy_index = 0

    def _get_next_proxy(self) -> str:
        proxy = self.PROXIES[self.proxy_index]
        self.proxy_index = (self.proxy_index + 1) % len(self.PROXIES)
        return proxy

    def _get_proxied_api_url(self, file_id: str) -> str:
        proxy_domain = self._get_next_proxy()
        return f"https://{proxy_domain}/api/file/{file_id}?download"

    def _get_direct_api_url(self, file_id: str) -> str:
        return f"https://pixeldrain.com/api/file/{file_id}"

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes <= 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"

    def export(self) -> Generator[Tuple[str, str], None, None]:
        """
        Yields a tuple of (filename, file_id) for each file found.
        Handles both single file pages (/u/) and lists (/l/).
        """
        print(f"[INFO] PixelDrain: Fetching page: {self.url}")
        try:
            res = self.session.get(self.url, timeout=30)
            res.raise_for_status()
            match = re.search(r"window\.viewer_data\s*=\s*({.*?});", res.text)
            if not match:
                raise ValueError("Could not find viewer_data JSON on page.")
            data = json.loads(match.group(1))
            api_response = data.get("api_response", {})
            files_to_process = []

            # Case 1: It's a list of files (/l/...)
            if data.get("type") == "list" and "files" in api_response:
                files_to_process = api_response["files"]
                total_size = sum(file.get("size", 0) for file in files_to_process)
                print(
                    f"[INFO] PixelDrain: Found list '{api_response.get('title')}' with {len(files_to_process)} files. "
                    f"Total size: {self._format_size(total_size)}"
                )

            # Case 2: It's a single file (/u/...)
            elif "name" in api_response:
                files_to_process = [api_response]
                print(
                    f"[INFO] PixelDrain: Found single file: '{api_response['name']}' "
                    f"({self._format_size(api_response.get('size', 0))})"
                )

            for file in files_to_process:
                # Yield filename and file_id for each file found
                yield (file["name"], file["id"])
        except (requests.RequestException, ValueError, KeyError) as e:
            print(f"[ERROR] PixelDrain: Error exporting from {self.url}: {e}")

    def download_file(self, item: Tuple[str, str], output_dir: str) -> Optional[bool]:
        """
        Downloads a single file using its filename and file_id.
        The `item` is expected to be a tuple (filename, file_id).
        """
        # Unpack the item yielded by export
        if not isinstance(item, tuple) or len(item) != 2:
            print(f"[ERROR] PixelDrain: Invalid item format for download_file: {item}")
            return False
        filename, file_id = item

        # Default to direct download
        # TODO: Allow proxy usage via plugin_kwargs
        use_proxy = False

        if use_proxy:
            download_url = self._get_proxied_api_url(file_id)
            source_msg = f"via PROXY {urlparse(download_url).hostname}"
        else:
            download_url = self._get_direct_api_url(file_id)
            source_msg = "directly from pixeldrain.com"

        print(f"[INFO] PixelDrain: Downloading '{filename}' {source_msg}...")
        try:
            os.makedirs(output_dir, exist_ok=True)
            save_path = os.path.join(output_dir, filename)

            with requests.get(
                download_url,
                stream=True,
                allow_redirects=True,
                headers=self.session.headers,
                timeout=60,
            ) as r:
                r.raise_for_status()
                with open(save_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:  # Filter out keep-alive chunks
                            f.write(chunk)
            print(f"[SUCCESS] PixelDrain: Downloaded '{filename}'")
            return True
        except Exception as e:
            print(f"[ERROR] PixelDrain: Download failed for '{filename}': {e}")
            return False
