import os
import re
import requests
from megaloader.http import http_download

ALBUM_REGEX = r"https?:\/\/cdn\d*\.bunkr\.ru\/[a-zA-Z0-9\-\.\_]+"
SINGLE_FILE_REGEX = r"https?:\/\/media-files\d*\.bunkr\.ru\/[a-zA-Z0-9\-\.\_]+"
FILE_IN_ALBUM_REGEX = r'<a href="(/d/[a-zA-Z0-9\-\.\_]+)"'


class Bunkr:
    """
    A class used to download files from Bunkr
    """

    def __init__(self, url: str):
        self.__url = url

    @property
    def url(self):
        return self.__url

    def build_direct_url(self, url: str) -> str:
        """
        Returns the direct URL for downloading the file based on media type
        """
        image_exts = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
        video_exts = [".mp4", ".mkv", ".wmv", ".webm"]

        if any(ext in url for ext in image_exts):
            final_url = re.sub(r"cdn(\d*)\.bunkr", r"i\1.bunkr", url)
        elif any(ext in url for ext in video_exts):
            final_url = re.sub(r"cdn\d*\.bunkr", "media-files.bunkr", url)
        elif url.startswith("/d/"):
            final_url = f"https://media-files.bunkr.ru/{url[3:]}"
        elif "bunkrr.su/d/" in url:
            final_url = re.sub(r"bunkr\.su\/d\/", "media-files11.bunkr.ru/", url)
        else:
            final_url = url

        return final_url

    def export(self):
        """
        Yields download URLs for files found on the Bunkr page
        """
        try:
            response = requests.get(self.url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while trying to fetch the URL: {e}")
            return

        seen_urls = set()

        # Find album URLs
        cdn_urls = re.findall(ALBUM_REGEX, response.text)
        for url in cdn_urls:
            url = self.build_direct_url(url)
            if url not in seen_urls:
                seen_urls.add(url)
                yield url

        # Find file URLs in album
        file_in_album_urls = re.findall(FILE_IN_ALBUM_REGEX, response.text)
        for url in file_in_album_urls:
            url = self.build_direct_url(url)
            if url not in seen_urls:
                seen_urls.add(url)
                yield url

        # Find single file URLs
        single_file_urls = re.findall(SINGLE_FILE_REGEX, response.text)
        for url in single_file_urls:
            url = self.build_direct_url(url)
            if url not in seen_urls:
                seen_urls.add(url)
                yield url

    def download_file(self, url: str, output: str):
        """
        Downloads a file and saves it to the specified output directory
        """
        try:
            http_download(url, output)
            filename = url.split("/")[-1]
            print(f"Downloaded {url} as {filename} to {output}")

        except Exception as e:
            print(f"An error occurred while trying to download the file: {e}")
