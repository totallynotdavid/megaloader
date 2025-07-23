import re
import requests
from megaloader.http import http_download


class ThothubVIP:
    BASE_URL = "https://thothub.vip/"
    REGEX_VIDEOS = re.compile(
        r"<source.*<img.*(http[s]?:\/\/(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)",
        re.M,
    )
    REGEX_IMAGES = re.compile(
        r"<img.*(http[s]?:\/\/(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)",
        re.M,
    )

    def __init__(self, tag: str):
        self.BASE_URL += tag

    def __get_page(self):
        url = self.BASE_URL
        response = requests.get(url)
        body = response.text
        if "Ooops, sorry! We couldn't find it" in body or response.code == 404:
            return ""
        return body

    def export(self):
        for match in self.REGEX_VIDEOS.findall(self.__get_page()):
            if match:
                yield match
        for match in self.REGEX_IMAGES.findall(self.__get_page()):
            if match:
                yield match

    def download_file(self, url: str, output: str):
        http_download(
            url,
            output,
            custom_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15",
            },
        )
