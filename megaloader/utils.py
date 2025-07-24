import html


def unentitify(text: str) -> str:
    """Converts HTML entities in a string to their corresponding characters."""
    if not isinstance(text, str) or not text:
        return text
    # html.unescape handles a wide range of named and numeric entities
    return html.unescape(text)
