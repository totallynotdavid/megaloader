import pytest

from megaloader.plugins import bunkr, cyberdrop, pixiv, thothub_to, thothub_vip


@pytest.mark.unit
@pytest.mark.parametrize(
    ("parse_target", "url"),
    [
        (bunkr.parse_target, "https://bunkr.si/other"),
        (cyberdrop.parse_target, "https://cyberdrop.cr/nope"),
        (thothub_vip.parse_target, "https://thothub.vip/unknown"),
    ],
)
def test_unrecognised_url_shape_has_no_target(parse_target, url: str) -> None:
    assert parse_target(url) is None


@pytest.mark.unit
@pytest.mark.parametrize(
    "url",
    [
        "https://www.pixiv.net/users/456",
        "https://www.pixiv.net/en/users/456",
        "https://www.pixiv.net/member.php?id=456",
    ],
)
def test_pixiv_user_urls_are_a_user(url: str) -> None:
    assert pixiv.parse_target(url) == pixiv.User("456")


@pytest.mark.unit
def test_pixiv_url_without_artwork_or_user_is_rejected() -> None:
    with pytest.raises(ValueError, match="Invalid Pixiv URL"):
        pixiv.parse_target("https://www.pixiv.net/")


@pytest.mark.unit
@pytest.mark.parametrize(
    ("module", "url"),
    [
        (thothub_to, "https://thothub.to/models/x/"),
        (thothub_vip, "https://thothub.vip/models/x/"),
    ],
)
def test_thothub_model_url_is_a_model(module, url: str) -> None:
    assert isinstance(module.parse_target(url), module.Model)
