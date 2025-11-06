"""Views for the downloader app."""

from typing import Any

from django.conf import settings
from django.shortcuts import render
from megaloader import download
from megaloader.plugins import PLUGIN_REGISTRY, get_plugin_class


def index(request):
    """Display the main download form and supported platforms."""
    context: dict[str, Any] = {
        "plugins": [
            {
                "name": plugin_class.__name__,
                "domains": ", ".join(domains)
                if isinstance(domains, tuple)
                else domains,
            }
            for domains, plugin_class in PLUGIN_REGISTRY.items()
        ]
    }

    if request.method == "POST":
        url = request.POST.get("url", "").strip()
        use_proxy = request.POST.get("use_proxy") == "on"
        create_subdirs = request.POST.get("create_subdirs", "on") == "on"

        if url:
            try:
                # Detect plugin
                plugin_class = get_plugin_class(url)

                # Download
                success = download(
                    url,
                    str(settings.DOWNLOAD_DIR),
                    plugin_class=plugin_class,
                    use_proxy=use_proxy,
                    create_album_subdirs=create_subdirs,
                )

                if success:
                    context["success"] = f"Successfully downloaded from {url}"
                else:
                    context["error"] = "Download failed"
            except Exception as e:
                context["error"] = f"Error: {e!s}"
        else:
            context["error"] = "Please provide a URL"

    return render(request, "downloader/index.html", context)


def about(request):
    """Display information about the demo."""
    return render(request, "downloader/about.html")
