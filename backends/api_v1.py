"""
Module that defines the user api v1 which goes through django-ninja.
"""

import json
from typing import List
import datetime
import uuid


from ninja import NinjaAPI
from ninja.responses import codes_4xx

from django.contrib.auth import authenticate

from dropbox.exceptions import ApiError, AuthError

from .schemas import BackendSchemaOut, JobSchemaIn, JobResponseSchema
from .apps import BackendsConfig as ac

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
    storage_provider = getattr(ac, "storage")
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
    storage_provider = getattr(ac, "storage")
    backend_names = storage_provider.get_backends()
    if not backend_name in backend_names:
        job_response_dict["status"] = "ERROR"
        job_response_dict["detail"] = "Unknown back-end!"
        job_response_dict["error_message"] = "Unknown back-end!"
        return 404, job_response_dict

    try:
        job_data = data.job.encode("utf-8")
    except UnicodeDecodeError:
        job_response_dict["status"] = "ERROR"
        job_response_dict["detail"] = "The encoding of your json seems non utf-8!"
        job_response_dict[
            "error_message"
        ] = "The encoding of your json seems non utf-8!"
        return 406, job_response_dict
    try:
        job_id = (
            (datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S"))
            + "-"
            + backend_name
            + "-"
            + username
            + "-"
            + (uuid.uuid4().hex)[:5]
        )
        job_json_dir = "/Backend_files/Queued_Jobs/" + backend_name + "/"
        job_json_name = "job-" + job_id + ".json"
        job_json_path = job_json_dir + job_json_name

        storage_provider = getattr(ac, "storage")
        storage_provider.upload(
            dump_str=job_data.decode("utf-8"), storage_path=job_json_path
        )
        status_json_dir = "/Backend_files/Status/" + backend_name + "/" + username + "/"
        status_json_name = "status-" + job_id + ".json"
        status_json_path = status_json_dir + status_json_name
        job_response_dict["job_id"] = job_id
        job_response_dict["status"] = "INITIALIZING"
        job_response_dict["detail"] = "Got your json."
        status_str = json.dumps(job_response_dict)
        storage_provider.upload(dump_str=status_str, storage_path=status_json_path)
        return job_response_dict
    except (AuthError, ApiError):
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
    storage_provider = getattr(ac, "storage")
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
        extracted_username = job_id.split("-")[2]
    except:
        job_response_dict["status"] = "ERROR"
        job_response_dict["detail"] = "Error loading json data from input request!"
        job_response_dict[
            "error_message"
        ] = "Error loading json data from input request!"
        return 406, job_response_dict
    try:
        status_json_dir = (
            "/Backend_files/Status/" + backend_name + "/" + extracted_username + "/"
        )
        status_json_name = "status-" + job_id + ".json"
        status_json_path = status_json_dir + status_json_name

        storage_provider = getattr(ac, "storage")
        job_response_dict = json.loads(
            storage_provider.get_file_content(storage_path=status_json_path)
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
    storage_provider = getattr(ac, "storage")
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
        extracted_username = job_id.split("-")[2]
    except:
        status_msg_dict["detail"] = "Error loading json data from input request!"
        status_msg_dict["error_message"] = "Error loading json data from input request!"
        return 406, status_msg_dict

    # request the data from the queue
    try:
        status_json_dir = (
            "/Backend_files/Status/" + backend_name + "/" + extracted_username + "/"
        )
        status_json_name = "status-" + job_id + ".json"
        status_json_path = status_json_dir + status_json_name
        storage_provider = getattr(ac, "storage")
        status_msg_dict = json.loads(
            storage_provider.get_file_content(storage_path=status_json_path)
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
        result_json_dir = (
            "/Backend_files/Result/" + backend_name + "/" + extracted_username + "/"
        )
        result_json_name = "result-" + job_id + ".json"
        result_json_path = result_json_dir + result_json_name
        storage_provider = getattr(ac, "storage")
        result_dict = json.loads(
            storage_provider.get_file_content(storage_path=result_json_path)
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
    storage_provider = getattr(ac, "storage")
    backend_names = storage_provider.get_backends()
    backend_list = []
    for backend in backend_names:
        # for testing we created dummy devices. We should ignore them in any other cases.
        if not "dummy_" in backend:
            config_dict = storage_provider.get_backend_dict(backend)
            backend_list.append(config_dict)
    return backend_list
