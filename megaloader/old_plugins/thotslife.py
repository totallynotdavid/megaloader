import re
import json
import requests
from megaloader import unentitify
from megaloader.http import http_download


class ThotslifeResource:
    REGEX_GALLERY = re.compile(
        r"<figure class=\".+\" id=\".+\" data-g1-gallery-title=\"\" data-g1-gallery=\"(\[.*\])\" data-g1-share-shortlink=\"https:\/\/thotslife\.com\/.+\/#.+\">"
    )
    REGEX_MEDIA_VIDEO = re.compile(
        r"^<source src=\"(https:\/\/.+thotslife\.com\/.+)\" label=\"\" type=\"video\/mp4\" \/>$",
        re.M,
    )
    REGEX_MEDIA_IMAGE = re.compile(
        r"^<a href='(https:\/\/thotslife\.com\/wp-content\/uploads\/.+)'>", re.M
    )

    def __init__(self, html: str):
        self.__html = html

    @property
    def gallery(self):
        for gallery in self.REGEX_GALLERY.findall(self.__html):
            gallery = json.loads(unentitify(gallery))
            for item in gallery:
                if "full" in item.keys():
                    yield item["full"]

    @property
    def media(self):
        for m in self.REGEX_MEDIA_VIDEO.findall(self.__html):
            yield m
        for m in self.REGEX_MEDIA_IMAGE.findall(self.__html):
            yield m


class Thotslife:
    BASE_URL = "https://thotslife.com/tag/"
    REGEX_RESOURCES = re.compile(
        r"<a title=\".+\" class=\"g1-frame\" href=\"(https:\/\/thotslife\.com\/.+\/)\">"
    )

    def __init__(self, tag: str):
        self.BASE_URL += tag

    def __get_page(self, page: int):
        url = self.BASE_URL
        if page > 1:
            url += "/page/{}/".format(page)
        response = requests.get(url)
        body = response.text
        if "Ooops, sorry! We couldn't find it" in body or response.code == 404:
            return ""
        return body

    def __get_pages(self):
        i = 1
        while True:
            page = self.__get_page(i)
            if page == "":
                break
            yield page
            i += 1

    def get_resources(self):
        for page in self.__get_pages():
            for url in self.REGEX_RESOURCES.findall(page):
                yield ThotslifeResource(requests.get(url).text)

    def export(self):
        for resource in self.get_resources():
            for g in resource.gallery:
                yield g
            for m in resource.media:
                yield m

    @staticmethod
    def download_file(url: str, output: str):
        http_download(
            url,
            output,
            custom_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "User-Agent": " (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
                "Referer": "",
                "Origin": "",
                "Connection": "",
                "Sec-Fetch-Dest": "",
                "Sec-Fetch-Mode": "",
                "Sec-Fetch-Site": "",
                "Pragma": "",
                "Cache-Control": "",
            },
        )
