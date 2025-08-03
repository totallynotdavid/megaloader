import re

import requests

from megaloader.http import http_download


BASE_API_URL = "https://api.fanbox.cc"


class Fanbox:
    def __init__(self, url: str):
        self.__creator = None
        self.__creator_id = None
        match = re.search(r"^https://([a-zA-Z0-9_\-\~]+)\.fanbox\.cc", url)

        if not match:
            raise ValueError("Invalid fanbox url provided.")
        self.__creator_id = match[1]
        self.__creator = self.execute_api("/creator.get")

    @property
    def creator_id(self):
        return self.__creator_id

    @property
    def creator(self):
        return self.__creator

    @property
    def paginate_creator(self):
        return self.execute_api("/post.paginateCreator")

    @property
    def banner(self):
        return self.creator["coverImageUrl"]

    @property
    def posts(self):
        for url in self.paginate_creator:
            response = self.execute_api(url)
            for post in response["items"]:
                response = self.execute_api("/post.info?postId=" + post["id"], False)
                if (
                    "body" in response
                    and response["body"] is not None
                    and "images" in response["body"]
                ):
                    for image in response["body"]["images"]:
                        yield image["originalUrl"]
                else:
                    yield response["coverImageUrl"]

    @property
    def carousel(self):
        response = self.execute_api("/creator.get")
        for i in response["profileItems"]:
            yield i["imageUrl"]

    @property
    def plan_thumbnails(self):
        response = self.execute_api("/plan.listCreator")
        for p in response:
            if p.get("coverImageUrl"):
                yield p["coverImageUrl"]

    def execute_api(self, endpoint: str, required_creator_id: bool = True):
        endpoint = endpoint.replace(BASE_API_URL, "")
        url = BASE_API_URL + endpoint
        if required_creator_id and "creatorId" not in url:
            url += (
                ("&" if endpoint.startswith("?") else "?")
                + "creatorId="
                + self.creator_id
            )
        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0",
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://" + self.creator_id + ".fanbox.cc/",
                "Origin": "https://" + self.creator_id + ".fanbox.cc",
            },
        ).json()
        if "body" in response:
            return response["body"]
        if "items" in response:
            return response["items"]
        return response

    def export(self):
        yield self.banner
        for e in self.plan_thumbnails:
            yield e
        for e in self.carousel:
            yield e
        for e in self.posts:
            yield e

    def download_file(self, url: str, output: str):
        http_download(url, output, custom_headers={"Accept": "gzip, deflate, br"})
