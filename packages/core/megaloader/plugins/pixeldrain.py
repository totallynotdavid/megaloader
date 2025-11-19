import json
import logging
import re

from collections.abc import Generator

from megaloader.plugin import BasePlugin, Item


logger = logging.getLogger(__name__)


class PixelDrain(BasePlugin):
    def extract(self) -> Generator[Item, None, None]:
        logger.info("Processing PixelDrain URL: %s", self.url)
        response = self.session.get(self.url, timeout=30)
        response.raise_for_status()

        match = re.search(
            r"window\.viewer_data\s*=\s*({.*?});", response.text, re.DOTALL
        )
        if not match:
            msg = "Could not find viewer data on page"
            raise ValueError(msg)

        data = json.loads(match.group(1))
        api_response = data.get("api_response", {})

        if data.get("type") == "list" and "files" in api_response:
            for f in api_response["files"]:
                yield Item(
                    url=f"https://pixeldrain.com/api/file/{f['id']}",
                    filename=f["name"],
                    id=f["id"],
                    meta={"size": f.get("size")},
                )
        elif "name" in api_response:
            yield Item(
                url=f"https://pixeldrain.com/api/file/{api_response['id']}",
                filename=api_response["name"],
                id=api_response["id"],
                meta={"size": api_response.get("size")},
            )
