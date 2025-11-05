import pytest

from megaloader.plugin import Item
from megaloader.plugins.pixeldrain import PixelDrain


@pytest.mark.integration
class TestPixelDrainIntegration:
    def test_single_file_parsing(self, requests_mock) -> None:
        url = "https://pixeldrain.com/u/testid"

        html = """
        <html><script>
        window.viewer_data = {"type":"file","api_response":{"id":"testid","name":"photo.jpg","size":204800}};
        </script></html>
        """

        requests_mock.get(url, text=html)

        plugin = PixelDrain(url)
        items = list(plugin.export())

        assert len(items) == 1
        assert items[0].filename == "photo.jpg"
        assert items[0].file_id == "testid"

        assert items[0].metadata is not None
        assert items[0].metadata["size"] == 204800

    def test_list_parsing(self, requests_mock) -> None:
        url = "https://pixeldrain.com/l/listid"

        html = """
        <html><script>
        window.viewer_data = {"type":"list","api_response":{"id":"listid","files":[
            {"id":"f1","name":"video.mp4","size":1048576},
            {"id":"f2","name":"image.png","size":512000}
        ]}};
        </script></html>
        """

        requests_mock.get(url, text=html)

        plugin = PixelDrain(url)
        items = list(plugin.export())

        assert len(items) == 2
        assert items[0].filename == "video.mp4"
        assert items[1].filename == "image.png"

    def test_proxy_rotation(self) -> None:
        plugin = PixelDrain("https://pixeldrain.com/u/test", use_proxy=True)

        url1 = plugin._get_download_url("file1")
        url2 = plugin._get_download_url("file2")

        assert "sriflix.my" in url1
        assert "sriflix.my" in url2
        assert "file1" in url1
        assert "file2" in url2

    def test_download_success(self, requests_mock, tmp_output_dir) -> None:
        url = "https://pixeldrain.com/api/file/testid"
        content = b"image data here"

        requests_mock.get(url, content=content)

        plugin = PixelDrain("https://pixeldrain.com/u/test")
        item = Item(url=url, filename="test.jpg", file_id="testid")

        result = plugin.download_file(item, tmp_output_dir)

        assert result is True

        import os

        path = os.path.join(tmp_output_dir, "test.jpg")
        assert os.path.exists(path)
        with open(path, "rb") as f:
            assert f.read() == content
