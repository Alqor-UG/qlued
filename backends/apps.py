"""
Module that configures the app.
"""
from django.apps import AppConfig


class BackendsConfig(AppConfig):
    """
    Class that defines some basic configuration settings.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "backends"
