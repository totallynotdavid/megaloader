import json

import pytest

from megaloader.plugins.thothub_to import ThothubTO
from megaloader.plugins.thothub_vip import ThothubVIP

from tests.helpers import fake_fetcher


TITLES = [
    ("AC/DC live", "AC_DC live.mp4"),
    ("Back\\slash", "Back_slash.mp4"),
    ("Wait... what", "Wait... what.mp4"),
]


@pytest.mark.unit
@pytest.mark.parametrize(("title", "filename"), TITLES)
def test_thothub_vip_video_title_names_the_file(title: str, filename: str) -> None:
    url = "https://thothub.vip/video/1/clip/"
    metadata = json.dumps({"contentUrl": "https://cdn.example/a.mp4", "name": title})
    page = f'<script type="application/ld+json">{metadata}</script>'

    items = list(ThothubVIP(url).extract(fake_fetcher({url: page})))

    assert [item.filename for item in items] == [filename]


@pytest.mark.unit
@pytest.mark.parametrize(("title", "filename"), TITLES)
def test_thothub_to_video_title_names_the_file(title: str, filename: str) -> None:
    url = "https://thothub.to/videos/1/clip/"
    video_url = (
        "function/0/https://cdn.example/get_file/1/" + "a" * 32 + "/1000/1/1.mp4/"
    )
    page = (
        f"<h1>{title}</h1><script>video_id: '1', video_url: '{video_url}', "
        "license_code: '$440571814535234',</script>"
    )

    items = list(ThothubTO(url).extract(fake_fetcher({url: page})))

    assert [item.filename for item in items] == [filename]
