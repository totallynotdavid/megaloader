import pytest


@pytest.mark.live
@pytest.mark.downloads_file
class TestPixelDrainLive:
    def test_pixeldrain_images_list(self):
        """Test against real PixelDrain images list with sample files"""
        from megaloader.plugins.pixeldrain import PixelDrain

        url = "https://pixeldrain.com/l/DDGtvvTU"

        try:
            plugin = PixelDrain(url)
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
                assert item.metadata.get("size", 0) > 0
        except Exception as e:
            pytest.skip(f"PixelDrain images list unavailable: {e}")

    def test_pixeldrain_videos_list(self):
        """Test against real PixelDrain videos list with sample files"""
        from megaloader.plugins.pixeldrain import PixelDrain

        url = "https://pixeldrain.com/l/zqoz6uFE"

        try:
            plugin = PixelDrain(url)
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
                assert item.metadata.get("size", 0) > 0
        except Exception as e:
            pytest.skip(f"PixelDrain videos list unavailable: {e}")
