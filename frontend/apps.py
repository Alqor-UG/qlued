"""
Module that configues the app.
"""

from django.apps import AppConfig


class FrontEndConfig(AppConfig):
    """
    Class that defines some basic configuration settings.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "frontend"
