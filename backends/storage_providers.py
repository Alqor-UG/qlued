"""
The module that contains all the necessary logic for communication with the external
storage for the jobs.
"""


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
