import logging


class EscapingFormatter(logging.Formatter):
    """Prevents log injection by escaping newlines in the final formatted string."""

    def format(self, record: logging.LogRecord) -> str:
        s = super().format(record)
        return s.replace("\r\n", r"\n").replace("\r", r"\n").replace("\n", r"\n")
