import pytest

from megaloader.plugins import bunkr, cyberdrop, pixiv, thothub_to, thothub_vip


@pytest.mark.unit
def test_bunkr_target_routing() -> None:
    assert bunkr.parse_target("https://bunkr.si/a/abc") == bunkr.Album(
        "https://bunkr.si/a/abc"
    )
    assert bunkr.parse_target("https://bunkr.si/f/xyz") == bunkr.File(
        "https://bunkr.si/f/xyz"
    )
    assert bunkr.parse_target("https://bunkr.si/other") is None


@pytest.mark.unit
def test_cyberdrop_target_routing() -> None:
    assert cyberdrop.parse_target("https://cyberdrop.cr/a/abc") == cyberdrop.Album(
        "https://cyberdrop.cr/a/abc"
    )
    assert cyberdrop.parse_target("https://cyberdrop.cr/f/xyz123") == cyberdrop.File(
        "xyz123"
    )
    assert cyberdrop.parse_target("https://cyberdrop.cr/nope") is None


@pytest.mark.unit
def test_pixiv_target_routing() -> None:
    assert pixiv.parse_target("https://www.pixiv.net/en/artworks/51400046") == (
        pixiv.Artwork("51400046")
    )
    assert pixiv.parse_target("https://www.pixiv.net/users/123") == pixiv.User("123")
    assert pixiv.parse_target("https://www.pixiv.net/member.php?id=456") == pixiv.User(
        "456"
    )

    with pytest.raises(ValueError, match="Invalid Pixiv URL"):
        pixiv.parse_target("https://www.pixiv.net/")


@pytest.mark.unit
def test_thothub_to_and_vip_target_routing() -> None:
    assert isinstance(
        thothub_to.parse_target("https://thothub.to/videos/1/x/"), thothub_to.Video
    )
    assert isinstance(
        thothub_to.parse_target("https://thothub.to/albums/1/x/"), thothub_to.Album
    )
    assert isinstance(
        thothub_vip.parse_target("https://thothub.vip/models/x/"), thothub_vip.Model
    )
    assert thothub_vip.parse_target("https://thothub.vip/unknown") is None
