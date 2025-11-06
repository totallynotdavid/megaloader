# Copy of megaloader plugin validation logic for Vercel deployment
from urllib.parse import urlparse


# Simplified plugin registry (domains that are supported)
PLUGIN_REGISTRY = {
    # Bunkr domains
    "bunkr.si": "Bunkr",
    "bunkr.la": "Bunkr",
    "bunkr.is": "Bunkr",
    # Cyberdrop domains
    "cyberdrop.me": "Cyberdrop",
    "cyberdrop.cc": "Cyberdrop",
    "cyberdrop.nl": "Cyberdrop",
    "cyberdrop.to": "Cyberdrop",
    "cyberdrop.ch": "Cyberdrop",
    "bunkr.ru": "Cyberdrop",
    "bunkr.su": "Cyberdrop",
    # GoFile
    "gofile.io": "Gofile",
    # PixelDrain
    "pixeldrain.com": "PixelDrain",
    # Pixiv
    "pixiv.net": "Pixiv",
    # Fanbox
    "fanbox.cc": "Fanbox",
    # Rule34
    "rule34.xxx": "Rule34",
    # Thothub
    "thothub.to": "ThothubTO",
    "thothub.vip": "ThothubVIP",
    # ThotsLife
    "thotslife.com": "Thotslife",
    # Fapello
    "fapello.com": "Fapello",
}

SUBDOMAIN_SUPPORTED_DOMAINS = {
    "gofile.io",
    "pixeldrain.com",
    "cyberdrop.me",
    "cyberdrop.cc",
    "cyberdrop.nl",
    "cyberdrop.to",
    "cyberdrop.ch",
}


def get_plugin_name(domain: str) -> str | None:
    """Get plugin name for a domain."""
    domain = domain.lower().strip()

    # Direct match first
    if domain in PLUGIN_REGISTRY:
        return PLUGIN_REGISTRY[domain]

    # Check for subdomain matches
    for supported_domain in SUBDOMAIN_SUPPORTED_DOMAINS:
        if (
            domain.endswith("." + supported_domain)
            and supported_domain in PLUGIN_REGISTRY
        ):
            return PLUGIN_REGISTRY[supported_domain]

    # Check if domain contains any known domain
    for key, plugin_name in PLUGIN_REGISTRY.items():
        if key in domain:
            return plugin_name

    return None


def handler(event, context):
    """Validate if a URL is supported by megaloader."""
    try:
        # Get URL from query parameter
        url = event.get("queryStringParameters", {}).get("url", "")

        if not url:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": '{"error": "Missing url parameter"}',
            }

        # Extract domain from URL
        try:
            domain = urlparse(url).netloc.lower()
            if not domain:
                domain = url.split("/")[0] if "/" in url else url
        except:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": '{"error": "Invalid URL format"}',
            }

        # Check if supported
        plugin_name = get_plugin_name(domain)

        if plugin_name:
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": f'{{"supported": true, "plugin": "{plugin_name}", "domain": "{domain}"}}',
            }
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": f'{{"supported": false, "domain": "{domain}"}}',
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": f'{{"error": "Server error: {e!s}"}}',
        }
