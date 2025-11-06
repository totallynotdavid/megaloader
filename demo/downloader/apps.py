"""Downloader app configuration."""

from django.apps import AppConfig


class DownloaderConfig(AppConfig):
    """Configuration for the downloader app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "downloader"
