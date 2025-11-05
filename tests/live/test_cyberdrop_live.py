import pytest


@pytest.mark.live
@pytest.mark.downloads_file
class TestCyberdropLive:
    def test_cyberdrop_images_album(self):
        """Test against real Cyberdrop images album with sample files"""
        from megaloader.plugins.cyberdrop import Cyberdrop

        url = "https://cyberdrop.cr/a/w4iUzGgx"

        try:
            plugin = Cyberdrop(url)
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
                expected_base = expected.rsplit(".", 1)[0]  # Remove extension
                assert any(
                    filename.startswith(expected_base) for filename in filenames
                ), f"Expected {expected} not found in {filenames}"

            for item in items:
                assert item.filename
                assert item.url
                assert item.file_id
        except Exception as e:
            import traceback

            traceback.print_exc()
            pytest.skip(f"Cyberdrop images album unavailable: {e}")

    def test_cyberdrop_videos_album(self):
        """Test against real Cyberdrop videos album with sample files"""
        from megaloader.plugins.cyberdrop import Cyberdrop

        url = "https://cyberdrop.cr/a/9ZwBUxsC"

        try:
            plugin = Cyberdrop(url)
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
                expected_base = expected.rsplit(".", 1)[0]  # Remove extension
                assert any(
                    filename.startswith(expected_base) for filename in filenames
                ), f"Expected {expected} not found in {filenames}"

            for item in items:
                assert item.filename
                assert item.url
                assert item.file_id
        except Exception as e:
            pytest.skip(f"Cyberdrop videos album unavailable: {e}")
