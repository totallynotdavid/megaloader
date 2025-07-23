import re
import requests
from megaloader.http import http_download

REGEX_VIDEO = r"^\s+<video.*src=\"(https:\/\/cdn.fapello.com\/content.+)\".*<\/video>$"
REGEX_IMAGE = r"^\s+<img src=\"(https:\/\/fapello.com\/content\/.+)\" alt=\".+\">$"


class Fapello:
    def __init__(self, url: str):
        self.model = None
        match = re.search(r"https://fapello.com/([a-zA-Z0-9_\-\~\.]+)", url)

        if not match:
            raise ValueError("Invalid fapello url provided.")
        self.model = match[1]

    def __get_all_ajax_pages(self):
        i = 0
        while True:
            url = "https://fapello.com/ajax/model/{}/page-{}/".format(self.model, i)
            page = requests.get(url)
            if len(page.text) < len("DOCTYPE"):
                break
            i += 1
            yield page.text

    @staticmethod
    def __get_hyper_text_links(page: str):
        return re.findall(r"https://fapello.com/[a-zA-Z0-9_\-\~\.]+/\d+", page, re.M)

    @staticmethod
    def __get_medias_from_page(page_url: str):
        page = requests.get(page_url).text
        f = re.findall(REGEX_VIDEO, page, re.M)
        f.extend(re.findall(REGEX_IMAGE, page, re.M))
        return f

    def export(self):
        for page in self.__get_all_ajax_pages():
            for l in self.__get_hyper_text_links(page):
                for e in self.__get_medias_from_page(l):
                    yield e

    @staticmethod
    def download(url: str, output: str):
        http_download(url, output)

    def download_file(self, url: str, output: str):
        http_download(url, output, custom_headers={"Accept": "gzip, deflate, br"})
