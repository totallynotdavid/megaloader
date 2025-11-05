import pytest


@pytest.mark.live
class TestGofileLive:
    def test_gofile_tokens(self):
        """Test that we can fetch real tokens"""
        from megaloader.plugins.gofile import Gofile

        plugin = Gofile("https://gofile.io/d/test")

        try:
            wt = plugin.website_token
            api = plugin.api_token

            assert wt and len(wt) > 0
            assert api and len(api) > 0
        except Exception as e:
            pytest.skip(f"Gofile API unreachable: {e}")

    def test_gofile_images_album(self):
        """Test against real Gofile images album with sample files"""
        from megaloader.plugins.gofile import Gofile

        url = "https://gofile.io/d/tiG4yG"

        try:
            plugin = Gofile(url)
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
                assert item.metadata is not None
                assert item.metadata.get("size") is not None
        except Exception as e:
            pytest.skip(f"Gofile images album unavailable: {e}")

    def test_gofile_videos_album(self):
        """Test against real Gofile videos album with sample files"""
        from megaloader.plugins.gofile import Gofile

        url = "https://gofile.io/d/xfjzT8"

        try:
            plugin = Gofile(url)
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
                assert item.metadata is not None
                assert item.metadata.get("size") is not None
        except Exception as e:
            pytest.skip(f"Gofile videos album unavailable: {e}")
