import math
import requests
import xml.etree.ElementTree as XML_ET
from megaloader.http import http_download


class Rule34:
    def __init__(self, tags: list):
        self.__tags = tags

    @property
    def tags(self):
        return self.__tags

    def api_url_builder(self, pid: int = 0, limit: int = 100):
        return "https://rule34.xxx/index.php?page=dapi&s=post&q=index&tags={}&pid={}&limit={}".format(
            ",".join(self.tags), pid, limit
        )

    def export(self):
        pid = 0
        limit = 100
        while True:
            url = self.api_url_builder(pid=pid)
            data = requests.get(url).text
            data = XML_ET.fromstringlist([data])
            total_posts = int(data.get("count"))
            posts = data.iter("post")
            for post in posts:
                yield post.get("file_url")
            pid_limit = math.ceil(total_posts / limit)
            if pid_limit == pid:
                break
            pid += 1

    def download_file(self, url: str, output: str):
        http_download(url, output, custom_headers={"Accept": "gzip, deflate, br"})
