import re
import requests
from megaloader.http import http_download


class Pixiv:
    def __init__(self, url: str, PHPSESSID: str = None):
        self.__creator_id = None
        self.__headers = {
            "Accept": "application/json",
        }
        match = re.search(r"https://www.pixiv.net/\w+/users/(\d+)", url)

        if not match:
            raise ValueError("Invalid pixiv url provided.")
        if PHPSESSID is not None:
            self.__headers["Cookie"] = "PHPSESSID=" + PHPSESSID
        self.__creator_id = match[1]

    @property
    def creator_id(self):
        return self.__creator_id

    def get_user_home(self, top_only: bool = False):
        return requests.get(
            "https://www.pixiv.net/ajax/user/"
            + self.creator_id
            + "/profile/"
            + ("top" if top_only else "all")
            + "?lang=en",
            headers=self.__headers,
        ).json()

    def get_user_home_illusts(self):
        return tuple(self.get_user_home()["body"]["illusts"].keys())

    def build_artwork_urls(self, artwork_id: str):
        # For loop to handle group illustrations.
        for illust in requests.get(
            "https://www.pixiv.net/ajax/illust/" + artwork_id + "/pages?lang=en",
            headers=self.__headers,
        ).json()["body"]:
            yield illust["urls"]["original"]

    def export(self):
        for artwork_id in self.get_user_home_illusts():
            for url in self.build_artwork_urls(artwork_id):
                yield url

    def download_file(self, url: str, output: str):
        http_download(url, output, custom_headers={"Accept": "gzip, deflate, br"})
