import html


def unentitify(text: str) -> str:
    """
    Decodes basic HTML entities in a string.

    Args:
        text (str): The string containing HTML entities.

    Returns:
        str: The string with entities decoded.
    """
    if not isinstance(text, str) or not text:
        return text
    # html.unescape handles a wide range of named and numeric entities
    return html.unescape(text)
