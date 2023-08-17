"""
Module that defines the user api v1 which goes through django-ninja.
"""

import json
from typing import List

from ninja import NinjaAPI
from ninja.responses import codes_4xx

from django.contrib.auth import authenticate

from dropbox.exceptions import ApiError, AuthError

from .schemas import BackendSchemaOut, JobSchemaIn, JobResponseSchema
from .storage_providers import get_storage_provider, get_storage_provider_from_entry
from .models import StorageProviderDb

api = NinjaAPI(version="1.0.0")


@api.get(
    "{backend_name}/get_config",
    response=BackendSchemaOut,
    tags=["Backend"],
    url_name="get_config",
)
def get_config(request, backend_name: str):
    """
    Returns the list of backends.
    """
    # pylint: disable=W0613
    storage_provider = get_storage_provider(backend_name)
    return storage_provider.get_backend_dict(backend_name, version="v1")


@api.post(
    "{backend_name}/post_job",
    response={200: JobResponseSchema, codes_4xx: JobResponseSchema},
    tags=["Backend"],
    url_name="post_job",
)
def post_job(request, data: JobSchemaIn, backend_name: str):
    """
    A view to submit the job to the backend.
    """
    # pylint: disable=R0914, W0613
    job_response_dict = {
        "job_id": "None",
        "status": "None",
        "detail": "None",
        "error_message": "None",
    }

    username = data.username
    password = data.password
    user = authenticate(username=username, password=password)

    if user is None:
        job_response_dict["status"] = "ERROR"
        job_response_dict["error_message"] = "Invalid credentials!"
        job_response_dict["detail"] = "Invalid credentials!"
        return 401, job_response_dict
    storage_provider = get_storage_provider(backend_name)
    backend_names = storage_provider.get_backends()
    if not backend_name in backend_names:
        job_response_dict["status"] = "ERROR"
        job_response_dict["detail"] = "Unknown back-end!"
        job_response_dict["error_message"] = "Unknown back-end!"
        return 404, job_response_dict

    try:
        job_dict = json.loads(data.job)
    except UnicodeDecodeError:
        job_response_dict["status"] = "ERROR"
        job_response_dict["detail"] = "The encoding of your json seems non utf-8!"
        job_response_dict[
            "error_message"
        ] = "The encoding of your json seems non utf-8!"
        return 406, job_response_dict
    try:
        # upload the job json to the backend through storage provider
        storage_provider = get_storage_provider(backend_name)

        job_id = storage_provider.upload_job(
            job_dict=job_dict, display_name=backend_name, username=username
        )

        # now we upload the status json to the backend. this is the same status json
        # that is returned to the user
        job_response_dict = storage_provider.upload_status(
            display_name=backend_name,
            username=username,
            job_id=job_id,
        )
        return job_response_dict
    except (AuthError, ApiError):
        print("Error saving json data to database!")
        job_response_dict["status"] = "ERROR"
        job_response_dict["detail"] = "Error saving json data to database!"
        job_response_dict["error_message"] = "Error saving json data to database!"
        return 406, job_response_dict


@api.get(
    "{backend_name}/get_job_status",
    response={200: JobResponseSchema, codes_4xx: JobResponseSchema},
    tags=["Backend"],
    url_name="get_job_status",
)
def get_job_status(
    request, backend_name: str, job_id: str, username: str, password: str
):
    """
    A view to check the job status that was previously submitted to the backend.
    """
    # pylint: disable=W0613
    job_response_dict = {
        "job_id": "None",
        "status": "None",
        "detail": "None",
        "error_message": "None",
    }

    user = authenticate(username=username, password=password)

    if user is None:
        job_response_dict["status"] = "ERROR"
        job_response_dict["error_message"] = "Invalid credentials!"
        job_response_dict["detail"] = "Invalid credentials!"
        return 401, job_response_dict

    storage_provider = get_storage_provider(backend_name)
    backend_names = storage_provider.get_backends()
    if not backend_name in backend_names:
        job_response_dict["status"] = "ERROR"
        job_response_dict["detail"] = "Unknown back-end!"
        job_response_dict["error_message"] = "Unknown back-end!"
        return 404, job_response_dict

    # complicated right now
    # pylint: disable=W0702
    try:
        job_response_dict["job_id"] = job_id
    except:
        job_response_dict["status"] = "ERROR"
        job_response_dict["detail"] = "Error loading json data from input request!"
        job_response_dict[
            "error_message"
        ] = "Error loading json data from input request!"
        return 406, job_response_dict
    try:
        # get the status json from the backend through storage provider
        storage_provider = get_storage_provider(backend_name)
        job_response_dict = storage_provider.get_status(
            display_name=backend_name, username=username, job_id=job_id
        )

        return 200, job_response_dict
    except:
        job_response_dict["status"] = "ERROR"
        job_response_dict[
            "detail"
        ] = "Error getting status from database. Maybe invalid JOB ID!"
        job_response_dict[
            "error_message"
        ] = "Error getting status from database. Maybe invalid JOB ID!"
        return 406, job_response_dict


@api.get(
    "{backend_name}/get_job_result",
    response={200: dict, codes_4xx: JobResponseSchema},
    tags=["Backend"],
    url_name="get_job_result",
)
def get_job_result(
    request, backend_name: str, job_id: str, username: str, password: str
):
    """
    A view to obtain the results of job that was previously submitted to the backend.
    """
    # pylint: disable=W0613, R0914, R0911
    status_msg_dict = {
        "job_id": "None",
        "status": "None",
        "detail": "None",
        "error_message": "None",
    }

    user = authenticate(username=username, password=password)

    if user is None:
        status_msg_dict["status"] = "ERROR"
        status_msg_dict["error_message"] = "Invalid credentials!"
        status_msg_dict["detail"] = "Invalid credentials!"
        return 401, status_msg_dict
    storage_provider = get_storage_provider(backend_name)
    backend_names = storage_provider.get_backends()
    if not backend_name in backend_names:
        status_msg_dict["status"] = "ERROR"
        status_msg_dict["detail"] = "Unknown back-end!"
        status_msg_dict["error_message"] = "Unknown back-end!"
        return 404, status_msg_dict

    # We should really handle these exceptions cleaner, but this seems a bit
    # complicated right now
    # pylint: disable=W0702
    # decode the job-id to request the data from the queue
    try:
        status_msg_dict["job_id"] = job_id
    except:
        status_msg_dict["detail"] = "Error loading json data from input request!"
        status_msg_dict["error_message"] = "Error loading json data from input request!"
        return 406, status_msg_dict

    # request the data from the queue
    try:
        status_msg_dict = storage_provider.get_status(
            display_name=backend_name, username=username, job_id=job_id
        )

        if status_msg_dict["status"] != "DONE":
            return 200, status_msg_dict
    except:
        status_msg_dict[
            "detail"
        ] = "Error getting status from database. Maybe invalid JOB ID!"
        status_msg_dict[
            "error_message"
        ] = "Error getting status from database. Maybe invalid JOB ID!"
        return 406, status_msg_dict
    # and if the status is switched to done, we can also obtain the result
    # one might attempt to connect this to the code above
    try:
        # now get the result from the database
        result_dict = storage_provider.get_result(
            display_name=backend_name, username=username, job_id=job_id
        )

        return 200, result_dict
    except:
        status_msg_dict["detail"] = "Error getting result from database!"
        status_msg_dict["error_message"] = "Error getting result from database!"
        return 406, status_msg_dict


@api.get(
    "/backends",
    response=List[BackendSchemaOut],
    tags=["Backend"],
    url_name="get_backends",
)
def list_backends(request):
    """
    Returns the list of backends, excluding any device called "dummy_" as they are test systems.
    """
    # pylint: disable=W0613, E1101
    backend_list = []
    # obtain all the available storage providers from the database
    storage_provider_entries = StorageProviderDb.objects.all()

    # now loop through them and obtain the backends
    for storage_provider_entry in storage_provider_entries:
        storage_provider = get_storage_provider_from_entry(storage_provider_entry)

        backend_names = storage_provider.get_backends()
        for backend in backend_names:
            # for testing we created dummy devices. We should ignore them in any other cases.
            if not "dummy_" in backend:
                config_dict = storage_provider.get_backend_dict(backend, version="v1")
                backend_list.append(config_dict)
    return backend_list
