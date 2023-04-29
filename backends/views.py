"""
Module that defines the user api.
"""
import datetime
import json
import uuid
from typing import Tuple
from decouple import config

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate

from dropbox.exceptions import ApiError, AuthError

from .apps import BackendsConfig as ac

# pylint: disable=E1101


def check_request(
    request, backend_name: str, req_method: str = "GET"
) -> Tuple[dict, int]:
    """
    A function that allows us to easily check if the request is valid

    Args:
        request: The request we would like to check
        backend_name: The backend we would like to use
        req_method: the method the user is allowed to call
    Returns:
        status, json_dict that has the appropiate answers
    """
    job_response_dict = {
        "job_id": "None",
        "status": "None",
        "detail": "None",
        "error_message": "None",
    }

    if not request.method == req_method:
        job_response_dict["status"] = "ERROR"
        job_response_dict["error_message"] = "Only " + req_method + " request allowed!"
        job_response_dict["detail"] = "Only " + req_method + " request allowed!"
        return job_response_dict, 405

    if req_method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
    elif req_method == "GET":
        username = request.GET["username"]
        password = request.GET["password"]
    else:
        raise NotImplementedError("Your method is unknown")
    user = authenticate(username=username, password=password)

    if user is None:
        job_response_dict["status"] = "ERROR"
        job_response_dict["error_message"] = "Invalid credentials!"
        job_response_dict["detail"] = "Invalid credentials!"
        return job_response_dict, 401
    storage_provider = getattr(ac, "storage")

    backend_names = storage_provider.get_backends()
    if not backend_name in backend_names:
        job_response_dict["status"] = "ERROR"
        job_response_dict["detail"] = "Unknown back-end!"
        job_response_dict["error_message"] = "Unknown back-end!"
        return job_response_dict, 404
    return job_response_dict, 200


# Create your views here.
@csrf_exempt
def get_config_v2(request, backend_name: str) -> JsonResponse:
    """
    A view that returns the user the configuration dictionary of the backend.

    Args:
        request: The request coming in
        backend_name (str): The name of the backend for the configuration should
            be obtained

    Returns:
        JsonResponse : send back a response with the dict if successful
    """
    job_response_dict, html_status = check_request(request, backend_name)

    if job_response_dict["status"] == "ERROR":
        return JsonResponse(job_response_dict, status=html_status)

    storage_provider = getattr(ac, "storage")
    backend_json_path = "Backend_files/Config/" + backend_name
    backend_config_dict = storage_provider.get_file_content(backend_json_path, "config")

    # for comaptibility with qiskit
    backend_config_dict["basis_gates"] = []
    for gate in backend_config_dict["gates"]:
        backend_config_dict["basis_gates"].append(gate["name"])

    backend_config_dict["backend_name"] = backend_config_dict["name"]
    backend_config_dict["display_name"] = backend_name
    backend_config_dict["n_qubits"] = backend_config_dict["num_wires"]
    backend_config_dict["backend_version"] = backend_config_dict["version"]

    backend_config_dict["conditional"] = False
    backend_config_dict["local"] = False
    backend_config_dict["open_pulse"] = False
    backend_config_dict["memory"] = True
    backend_config_dict["coupling_map"] = "linear"

    # and the url
    base_url = config("BASE_URL")
    backend_config_dict["url"] = base_url + "/api/" + backend_name + "/"

    return JsonResponse(backend_config_dict, status=200)


@csrf_exempt
def post_job(request, backend_name: str) -> JsonResponse:
    """
    A view to submit the job to the backend.

    Args:
        request: The request coming in
        backend_name (str): The name of the backend for the configuration should
            be obtained

    Returns:
        JsonResponse : send back a response with the dict if successful
    """
    job_response_dict, html_status = check_request(request, backend_name, "POST")
    if job_response_dict["status"] == "ERROR":
        return JsonResponse(job_response_dict, status=html_status)

    username = request.POST["username"]
    try:
        data = request.POST["json"].encode("utf-8")
    except UnicodeDecodeError:
        job_response_dict["status"] = "ERROR"
        job_response_dict["detail"] = "The encoding of your json seems non utf-8!"
        job_response_dict[
            "error_message"
        ] = "The encoding of your json seems non utf-8!"
        return JsonResponse(job_response_dict, status=406)
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
        job_json_name = "job-" + job_id

        storage_provider = getattr(ac, "storage")
        storage_provider.upload(json.loads(data), job_json_dir, job_json_name)

        status_json_dir = "Backend_files/Status/" + backend_name + "/" + username
        status_json_name = "status-" + job_id
        job_response_dict["job_id"] = job_id
        job_response_dict["status"] = "INITIALIZING"
        job_response_dict["detail"] = "Got your json."
        storage_provider.upload(job_response_dict, status_json_dir, status_json_name)
        return JsonResponse(job_response_dict)
    except (AuthError, ApiError):
        job_response_dict["status"] = "ERROR"
        job_response_dict["detail"] = "Error saving json data to database!"
        job_response_dict["error_message"] = "Error saving json data to database!"
        return JsonResponse(job_response_dict, status=406)


@csrf_exempt
def get_job_status(request, backend_name: str) -> JsonResponse:
    """
    A view to check the job status that was previously submitted to the backend.

    Args:
        request: The request coming in
        backend_name (str): The name of the backend for the configuration should
            be obtained

    Returns:
        JsonResponse : send back a response with the dict if successful
    """
    status_msg_dict, html_status = check_request(request, backend_name)
    if status_msg_dict["status"] == "ERROR":
        return JsonResponse(status_msg_dict, status=html_status)

    # We should really handle these exceptions cleaner, but this seems a bit
    # complicated right now
    # pylint: disable=W0702
    try:
        data = json.loads(request.GET["json"])
        job_id = data["job_id"]
        status_msg_dict["job_id"] = job_id
        extracted_username = job_id.split("-")[2]
    except:
        status_msg_dict["status"] = "ERROR"
        status_msg_dict["detail"] = "Error loading json data from input request!"
        status_msg_dict["error_message"] = "Error loading json data from input request!"
        return JsonResponse(status_msg_dict, status=406)
    try:
        status_json_dir = (
            "Backend_files/Status/" + backend_name + "/" + extracted_username
        )

        status_json_name = "status-" + job_id

        storage_provider = getattr(ac, "storage")
        status_msg_dict = storage_provider.get_file_content(
            status_json_dir, status_json_name
        )
        return JsonResponse(status_msg_dict, status=200)
    except:
        status_msg_dict["status"] = "ERROR"
        status_msg_dict[
            "detail"
        ] = "Error getting status from database. Maybe invalid JOB ID!"
        status_msg_dict[
            "error_message"
        ] = "Error getting status from database. Maybe invalid JOB ID!"
        return JsonResponse(status_msg_dict, status=406)


@csrf_exempt
def get_job_result(request, backend_name: str) -> JsonResponse:
    """
    A view to obtain the results of job that was previously submitted to the backend.

    Args:
        request: The request coming in
        backend_name (str): The name of the backend

    Returns:
        JsonResponse : send back a response with the dict if successful
    """
    status_msg_dict, html_status = check_request(request, backend_name)
    if status_msg_dict["status"] == "ERROR":
        return JsonResponse(status_msg_dict, status=html_status)

    # We should really handle these exceptions cleaner, but this seems a bit
    # complicated right now
    # pylint: disable=W0702

    # decode the job-id to request the data from the queue
    try:
        data = json.loads(request.GET["json"])
        job_id = data["job_id"]
        status_msg_dict["job_id"] = job_id
        extracted_username = job_id.split("-")[2]
    except:
        status_msg_dict["detail"] = "Error loading json data from input request!"
        status_msg_dict["error_message"] = "Error loading json data from input request!"
        return JsonResponse(status_msg_dict, status=406)

    # request the data from the queue
    try:
        status_json_dir = (
            "Backend_files/Status/" + backend_name + "/" + extracted_username
        )
        status_json_name = "status-" + job_id 
        storage_provider = getattr(ac, "storage")
        status_msg_dict = storage_provider.get_file_content(
            status_json_dir, status_json_name
        )

        if status_msg_dict["status"] != "DONE":
            return JsonResponse(status_msg_dict, status=200)
    except:
        status_msg_dict[
            "detail"
        ] = "Error getting status from database. Maybe invalid JOB ID!"
        status_msg_dict[
            "error_message"
        ] = "Error getting status from database. Maybe invalid JOB ID!"
        return JsonResponse(status_msg_dict, status=406)
    # and if the status is switched to done, we can also obtain the result
    # one might attempt to connect this to the code above
    try:
        result_json_dir = (
            "Backend_files/Result/" + backend_name + "/" + extracted_username 
        )
        result_json_name = "result-" + job_id
        storage_provider = getattr(ac, "storage")
        result_dict = storage_provider.get_file_content(
            result_json_dir, result_json_name
        )

        return JsonResponse(result_dict, status=200)
    except:
        status_msg_dict["detail"] = "Error getting result from database!"
        status_msg_dict["error_message"] = "Error getting result from database!"
        return JsonResponse(status_msg_dict, status=406)



@csrf_exempt
def get_user_jobs(request, backend_name: str) -> JsonResponse:
    """
    A view that all the jobs of a user for the specified backend

    Args:
        request: The request coming in
        backend_name (str): The name of the backend

    Returns:
        JsonResponse : send back a response with the dict if successful
    """
    status_msg_dict, html_status = check_request(request, backend_name)
    if status_msg_dict["status"] == "ERROR":
        return JsonResponse(status_msg_dict, status=html_status)

    user_job_dict = {"job_ids": "None"}
    username = request.GET["username"]
    # We should really handle these exceptions cleaner, but this seems a bit
    # complicated right now
    # pylint: disable=W0702
    try:
        job_json_dir = (
            "/Backend_files/Finished_Jobs/" + backend_name + "/" + username + "/"
        )
        storage_provider = getattr(ac, "storage")
        job_list = storage_provider.get_file_queue(job_json_dir)
        assert len(job_list) != 0
        job_list = [job_json_name[4:-5] for job_json_name in job_list]
        user_job_dict["job_ids"] = job_list
        return JsonResponse(user_job_dict)
    except:
        return JsonResponse(user_job_dict)
