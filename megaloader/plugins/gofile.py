import hashlib
import requests
from megaloader.http import http_download


class GoFile:
    def __init__(self, url: str, password: str = None):
        self.__password = None
        self.__content_id = url[len("https://gofile.io/d/") :]
        self.__api_key = self.__get_api_key()

        if password:
            self.__password = hashlib.sha256(password.encode()).hexdigest()

    @property
    def content_id(self):
        return self.__content_id

    @property
    def api_key(self):
        return self.__api_key

    @property
    def password(self):
        return self.__password

    @staticmethod
    def __get_api_key():
        data = requests.get("https://api.gofile.io/createAccount").json()
        api_token = data["data"]["token"]
        data = requests.get(
            "https://api.gofile.io/getAccountDetails?token=" + api_token
        ).json()
        if data["status"] != "ok":
            raise Exception("The account was not successfully activated.")
        return api_token

    def export(self):
        url = "https://api.gofile.io/getContent?contentId={}&token={}&websiteToken=7fd94ds12fds4"
        url = url.format(self.content_id, self.api_key)

        if self.password:
            url += "&password=" + self.password
        resources = requests.get(url).json()
        if "contents" in resources["data"].keys():
            contents = resources["data"]["contents"]
            for content in contents.values():
                yield content["link"]

    def download_file(self, url: str, output: str):
        http_download(
            url,
            output,
            custom_headers={
                "Cookie": "accountToken=" + self.api_key,
                "Accept-Encoding": "gzip, deflate, br",
            },
        )
