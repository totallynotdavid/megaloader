import re
import requests
from megaloader.http import http_download

REGEX_MEDIA = r"(?:https:\/\/)[^cdn\.][a-z0-9\-\/\.]+.cyberdrop.(?:to|me)\/[a-z0-9_\-A-Z \(\)\/]+.(?:mp4|mov|m4v|ts|mkv|avi|wmv|webm|vob|gifv|mpg|mpeg|mp3|flac|wav|png|jpeg|jpg|gif|bmp|webp|heif|heic|tiff|svf|svg|ico|psd|ai|pdf|txt|log|csv|xml|cbr|zip|rar|7z|tar|gz|xz|targz|tarxz|iso|torrent|kdbx)"


class Cyberdrop:
    def __init__(self, url: str) -> None:
        self.__url = url

    @property
    def url(self):
        return self.__url

    def export(self):
        response = requests.get(self.url)
        for url in re.findall(REGEX_MEDIA, response.text):
            if "/thumbs/" in url or "/s/" in url:
                continue
            if url.index("cyberdrop") < 14 or url.index("cyberdrop") > 18:
                continue
            yield url

    def download_file(self, url: str, output: str):
        http_download(url, output, custom_headers={"Accept": "gzip, deflate, br"})
