import pytest

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
        items = list(plugin.extract())

        assert len(items) == 1
        assert items[0].filename == "photo.jpg"
        assert items[0].id == "testid"

        assert items[0].meta is not None
        assert items[0].meta["size"] == 204800

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
        items = list(plugin.extract())

        assert len(items) == 2
        assert items[0].filename == "video.mp4"
        assert items[1].filename == "image.png"
