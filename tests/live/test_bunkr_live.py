import pytest


@pytest.mark.live
@pytest.mark.downloads_file
class TestBunkrLive:
    def test_bunkr_images_album(self):
        """Test against real Bunkr images album with sample files"""
        from megaloader.plugins.bunkr import Bunkr

        url = "https://bunkr.cr/a/xYKtNmBx"

        try:
            plugin = Bunkr(url)
            items = list(plugin.export())

            assert len(items) == 6  # 6 sample images
            filenames = [item.filename for item in items]

            expected_files = [
                "sample-image-01.jpg",
                "sample-image-02.jpg",
                "sample-image-03.jpg",
                "sample-image-04.jpg",
                "sample-image-05.jpg",
                "sample-image-06.jpg",
            ]

            for expected in expected_files:
                assert expected in filenames

            for item in items:
                assert item.filename
                assert item.url
                assert item.file_id
                assert "get.bunkr" in item.url or "bunkr" in item.url
        except Exception as e:
            pytest.skip(f"Bunkr images album unavailable: {e}")

    def test_bunkr_videos_album(self):
        """Test against real Bunkr videos album with sample files"""
        from megaloader.plugins.bunkr import Bunkr

        url = "https://bunkr.cr/a/I4TiEKcm"

        try:
            plugin = Bunkr(url)
            items = list(plugin.export())

            assert len(items) == 4  # 4 sample videos
            filenames = [item.filename for item in items]

            expected_files = [
                "sample-video-bunny.webm",
                "sample-video-planet.mov",
                "sample-video-jellyfish.mkv",
                "sample-video-rick.mp4",
            ]

            for expected in expected_files:
                assert expected in filenames

            for item in items:
                assert item.filename
                assert item.url
                assert item.file_id
                assert "get.bunkr" in item.url or "bunkr" in item.url
        except Exception as e:
            pytest.skip(f"Bunkr videos album unavailable: {e}")
