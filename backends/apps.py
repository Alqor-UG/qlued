"""
Module that configures the app.
"""
from django.apps import AppConfig

# at this stage we decide which storage provider we want to use.
# currently we have Dropbox and MongoDB.
from .storage_providers import MongodbProvider


class BackendsConfig(AppConfig):
    """
    Class that defines some basic configuration settings.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "backends"

    # use this to use the mongodb provider
    storage = MongodbProvider()

    # uncomment this to use the dropbox provider
    # storage = DropboxProvider()
