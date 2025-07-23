import requests
import re
import os
import base64
import math
from urllib.parse import urljoin, urlparse, quote
from typing import Generator, Optional
from bs4 import BeautifulSoup


class Bunkr:
    API_URL = "https://apidl.bunkr.ru/api/_001_v2"

    def __init__(self, url: str):
        self.url = url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )

    def _get_base_url(self, url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _solve_encrypted_url(
        self, api_response: dict, original_filename: str
    ) -> Optional[str]:
        try:
            timestamp = api_response["timestamp"]
            encrypted_url_b64 = api_response["url"]
            key_str = f"SECRET_KEY_{math.floor(timestamp / 3600)}"
            key_bytes = key_str.encode("utf-8")
            encrypted_bytes = base64.b64decode(encrypted_url_b64)
            decrypted_bytes = bytearray(len(encrypted_bytes))
            for i in range(len(encrypted_bytes)):
                decrypted_bytes[i] = encrypted_bytes[i] ^ key_bytes[i % len(key_bytes)]
            base_url = decrypted_bytes.decode("utf-8")
            return f"{base_url}?n={quote(original_filename)}"
        except (KeyError, TypeError, Exception) as e:
            print(f"Error decrypting URL: {e}")
            return None

    def export(self) -> Generator[str, None, None]:
        print(f"Fetching page: {self.url}")
        try:
            initial_res = self.session.get(self.url, allow_redirects=True)
            initial_res.raise_for_status()
            album_url = initial_res.url

            soup = BeautifulSoup(initial_res.text, "lxml")

            if "/a/" in album_url:
                print("Album page detected. Finding and resolving all file links...")
                links = soup.select('a[href^="/f/"]')

                if not links:
                    print("Warning: Could not find any file links on the album page.")
                    return

                print(f"Found {len(links)} items in album.")
                unique_urls = set()
                for i, link in enumerate(links, 1):
                    viewer_page_url = urljoin(
                        self._get_base_url(album_url), link["href"]
                    )

                    if viewer_page_url in unique_urls:
                        continue
                    unique_urls.add(viewer_page_url)

                    print(f"Resolving link {i}/{len(links)}: {viewer_page_url}")
                    try:
                        viewer_res = self.session.get(
                            viewer_page_url, allow_redirects=True
                        )
                        viewer_res.raise_for_status()
                        viewer_soup = BeautifulSoup(viewer_res.text, "lxml")

                        download_button = viewer_soup.find(
                            "a",
                            class_=["btn-main", "ic-download-01"],
                            string="Download",
                        )

                        if download_button and download_button.get("href"):
                            file_page_url = download_button["href"]
                            absolute_file_page_url = urljoin(
                                viewer_res.url, file_page_url
                            )
                            print(f"  -> Resolved to: {absolute_file_page_url}")
                            yield absolute_file_page_url
                        else:
                            print(
                                f"  -> Failed: Could not find the download button link on {viewer_page_url}"
                            )

                    except requests.RequestException as e:
                        print(f"  -> Failed to resolve {viewer_page_url}: {e}")

            else:
                print("Single file page detected. No album parsing needed.")
                yield album_url

        except requests.RequestException as e:
            print(f"Error fetching initial URL: {e}")

    def download_file(self, file_page_url: str, output_dir: str) -> Optional[str]:
        """
        Downloads a single file given its final file page URL (e.g., '.../file/...').
        """
        try:
            print(f"\n[1/4] Fetching metadata from: {file_page_url}")
            page_res = self.session.get(file_page_url)
            page_res.raise_for_status()
            soup = BeautifulSoup(page_res.text, "lxml")

            download_element = soup.find("a", id="download-btn")
            if not download_element or "data-id" not in download_element.attrs:
                raise ValueError(
                    "Could not find download element or its data-id on the final page."
                )
            file_id = download_element["data-id"]

            script_tag = soup.find("script", string=re.compile(r"var ogname\s*="))
            if not script_tag:
                raise ValueError("Could not find script tag with original filename.")

            match = re.search(r'var ogname\s*=\s*"(.*?)"', script_tag.string)
            if not match:
                raise ValueError("Could not extract original filename from script.")
            original_filename = match.group(1)

            print(f"  -> Found File ID: {file_id}, Filename: {original_filename}")

            print("[2/4] Requesting encrypted data from API...")
            api_res = self.session.post(self.API_URL, json={"id": file_id})
            api_res.raise_for_status()
            api_data = api_res.json()

            print("[3/4] Decrypting download link...")
            final_url = self._solve_encrypted_url(api_data, original_filename)
            if not final_url:
                raise ValueError("Failed to decrypt the download URL.")

            os.makedirs(output_dir, exist_ok=True)
            save_path = os.path.join(output_dir, original_filename)

            print(f"[4/4] Downloading to: {save_path}")

            headers = {"Referer": self._get_base_url(file_page_url) + "/"}
            with self.session.get(
                final_url, headers=headers, stream=True, allow_redirects=True
            ) as r:
                r.raise_for_status()
                with open(save_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            print("  -> Download complete!")
            return save_path

        except Exception as e:
            print(f"❌ Failed to download from {file_page_url}: {e}")
            return None
