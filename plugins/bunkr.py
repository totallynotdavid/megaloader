import re
import json
import requests
from megaloader.http import http_download

REGEX = r"https?:\/\/media-files\d+\.bunkr\.\w+\/[a-zA-Z0-9\-\.\_\&\?\+\%\(\)\[\]]+"

class Bunkr:
    def __init__(self, url: str):
        self.__url = url

    @property
    def url(self):
        return self.__url

    def export(self):
        response = requests.get(self.url)
        url = re.findall(REGEX, response.text)[0]
        yield url

    def download_file(self, url: str, output: str):
        http_download(url, output, custom_headers=None, headers_required=False)
