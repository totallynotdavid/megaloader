import re
import time
import requests


class ThothubTO:
    def __get_video_page(self, page_url: str):
        page = requests.get(page_url)
        if page.status_code == 404:
            return []
        return re.findall(r"\"(https:\/\/thothub.to\/videos\/\d+\/.*\/)\"", page.text)

    def __model_page(self, model: str):
        url = "https://thothub.to/models/{}/?".format(model)
        params = {
            "mode": "async",
            "function": "get_block",
            "block_id": "list_videos_common_videos_list",
            "sort_by": "post_date",
            "_": str(int(time.time())),
        }
        for k, v in params.items():
            url += k + "=" + v + "&"
        return url[:-1]

    def __get_video_pages(self, model_page: str):
        i = 1
        while True:
            url = model_page + "&form=" + str(i)
            captured_video_links = self.__get_video_page(url)
            if len(captured_video_links) == 0:
                break
            for link in captured_video_links:
                yield link
            i += 1

    def get_video_from_page(self, page_url: str):
        match = re.search(
            r"https:\/\/thothub.to\/get_file\/\d+\/[a-f0-9]+\/\d+\/\d+\/\d+.mp4",
            requests.get(page_url).text,
        )
        return None if match is None else match[0]

    def export(self, model: str):
        video_pages = self.__get_video_pages(self.__model_page(model))
        for page_url in video_pages:
            video_url = self.__get_video_from_page(page_url)
            if video_url is not None:
                yield video_url
