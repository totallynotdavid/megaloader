import logging

import requests

from megaloader import Bunkr, PixelDrain, download


# Internal logging: Enable debug logging from the megaloader package itself.
# Levels available: DEBUG, INFO, WARNING, ERROR, CRITICAL.
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(name)s: %(message)s")

# Automatic plugin detection.
download("https://pixeldrain.com/u/95u1wnsd", "./downloads")

# Inject a session with, e.g., retry logic.
session = requests.Session()
# Add your custom adapter/retry logic like this: session.mount(...)
download(
    "https://bunkrr.su/d/megaloader-main-RKEICuly.zip",
    "./downloads",
    session=session,
    plugin_class=Bunkr,
)

# Enable proxy usage for PixelDrain.
download(
    "https://pixeldrain.com/l/nH4ZKt3b",
    "./downloads",
    plugin_class=PixelDrain,
    use_proxy=True,
)

download("https://cyberdrop.me/a/0OpiyaOV", "./downloads")
