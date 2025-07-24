import logging
import requests
from megaloader import download, Bunkr, PixelDrain

# Internal logging: Enable debug logging from the megaloader package itself.
# Levels available: DEBUG, INFO, WARNING, ERROR, CRITICAL.
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(name)s: %(message)s")

# Automatic plugin detection.
download("https://pixeldrain.com/u/95u1wnsd", "./downloads")
print("Download complete.")
print(" ")

# Inject a session with, e.g., retry logic.
session = requests.Session()
# (Add your custom adapter/retry logic here)
# session.mount(...)
download(
    "https://bunkrr.su/d/megaloader-main-RKEICuly.zip",
    "./downloads",
    session=session,
    plugin_class=Bunkr,
)
print("Download complete.")
print(" ")

# Enable proxy usage for PixelDrain.
download(
    "https://pixeldrain.com/l/nH4ZKt3b",
    "./downloads",
    plugin_class=PixelDrain,
    use_proxy=True,
)
print("Download complete.")
print(" ")

download("https://bunkr.si/f/StoRbcXsF0Yje", "./downloads")
