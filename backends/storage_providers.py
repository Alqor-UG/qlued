"""
The module that contains all the necessary logic for communication with the external
storage for the jobs.
"""

from sqooler.storage_providers import (
    StorageProvider,
    MongodbProviderExtended,
    DropboxProviderExtended,
    LocalProviderExtended,
)

from sqooler.schemes import (
    MongodbLoginInformation,
    DropboxLoginInformation,
    LocalLoginInformation,
)

# get the environment variables
from decouple import config


def get_storage_provider(backend_name: str) -> StorageProvider:
    """
    Get the storage provider that is used for the backend.
    The storage provider that is used for the backend

    Args:
        backend_name: The full name of the backend

    Raises:
        ValueError: If the storage provider is not supported
    """

    # we have to import it here to avoid circular imports
    # pylint: disable=import-outside-toplevel
    from .models import StorageProviderDb

    # we often identify the backend by its short name. Let us use the assumption that this
    # means that we work with a default database. This is part of bug #152
    if len(backend_name.split("_")) == 1:
        storage_provider_name = config("DEFAULT_STORAGE", "alqor")
    else:
        storage_provider_name = backend_name.split("_")[0]

    storage_provider_entry = StorageProviderDb.objects.get(name=storage_provider_name)

    return get_storage_provider_from_entry(storage_provider_entry)


def get_storage_provider_from_entry(
    storage_provider_entry,
) -> StorageProvider:
    """
    Get the storage provider that is used for the backend.

    Args:
        storage_provider_entry: The entry from the Django database

    Returns:
        The storage provider that is used for the backend

    Raises:
        ValueError: If the storage provider is not supported
    """

    # pylint: disable=R1705
    # test if the storage provider is actually active or not
    if not storage_provider_entry.is_active:
        raise ValueError("The storage provider is not active.")

    # find the appropriate storage provider
    if storage_provider_entry.storage_type == "mongodb":
        login_info = MongodbLoginInformation(**storage_provider_entry.login)
        return MongodbProviderExtended(login_info, storage_provider_entry.name)
    elif storage_provider_entry.storage_type == "dropbox":
        login_info = DropboxLoginInformation(**storage_provider_entry.login)
        return DropboxProviderExtended(login_info, storage_provider_entry.name)
    elif storage_provider_entry.storage_type == "local":
        login_info = LocalLoginInformation(**storage_provider_entry.login)
        return LocalProviderExtended(login_info, storage_provider_entry.name)
    raise ValueError("The storage provider is not supported.")


def get_short_backend_name(backend_name: str) -> str:
    """
    Get the short name of the backend. If the name has only one part, it returns the name.
    If the name has multiple parts, it returns the middle part.
    Args:
        backend_name: The name of the backend

    Returns:
        The display_name of the backend
    """
    if len(backend_name.split("_")) == 1:
        display_name = backend_name
    elif len(backend_name.split("_")) == 3:
        # the first name is the name of the storage (this will become active with #148).
        _ = backend_name.split("_")[0]
        display_name = backend_name.split("_")[1]
        _ = backend_name.split("_")[2]
    else:
        display_name = ""
    return display_name
