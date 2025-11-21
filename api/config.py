import logging
import os
import sys

from typing import Literal


# Size limits
MAX_SIZE_MB = float(os.getenv("API_MAX_SIZE_MB", "4.0"))
MAX_SIZE_BYTES = int(MAX_SIZE_MB * 1024 * 1024)
MAX_FILE_COUNT = int(os.getenv("API_MAX_FILES", "50"))

# Timeouts
SIZE_CHECK_TIMEOUT = int(os.getenv("API_SIZE_CHECK_TIMEOUT", "5"))
DOWNLOAD_TIMEOUT = int(os.getenv("API_DOWNLOAD_TIMEOUT", "30"))

# Rate limiting (Upstash Redis)
UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_REST_URL", "")
UPSTASH_REDIS_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
RATE_LIMIT_REQUESTS = int(os.getenv("API_RATE_LIMIT_REQUESTS", "10"))
RATE_LIMIT_WINDOW = int(os.getenv("API_RATE_LIMIT_WINDOW", "60"))

# CORS
CORS_ORIGINS_STR = os.getenv("API_CORS_ORIGINS", "*")
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_STR.split(",")]

# Logging
LOG_LEVEL = os.getenv("API_LOG_LEVEL", "INFO")
LOG_FORMAT: Literal["json", "text"] = os.getenv("API_LOG_FORMAT", "json")  # type: ignore[assignment]

# Environment detection
IS_PRODUCTION = "VERCEL" in os.environ or os.getenv("ENV") == "production"

# Constants
UNKNOWN_CLIENT = "unknown"

# Whitelisted domains
ALLOWED_DOMAINS = frozenset(
    {
        "bunkr.si",
        "bunkr.la",
        "bunkr.is",
        "bunkr.ru",
        "bunkr.su",
        "pixeldrain.com",
        "cyberdrop.cr",
        "cyberdrop.me",
        "cyberdrop.to",
        "gofile.io",
    }
)


def configure_logging() -> None:
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)

    if LOG_FORMAT == "json":
        import json

        class JSONFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                log_data = {
                    "timestamp": self.formatTime(record),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                }

                if record.exc_info:
                    log_data["exception"] = self.formatException(record.exc_info)

                for key in ["client_ip", "url", "domain", "status_code"]:
                    if hasattr(record, key):
                        log_data[key] = getattr(record, key)

                return json.dumps(log_data)

        handler.setFormatter(JSONFormatter())
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Silence noisy libraries
    for lib in ["urllib3", "requests", "httpx", "uvicorn.access"]:
        logging.getLogger(lib).setLevel(logging.WARNING)
