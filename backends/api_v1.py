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

from decouple import config
from dropbox.exceptions import ApiError, AuthError

from .schemas import BackendSchemaOut, JobSchemaIn, JobResponseSchema
from .models import Backend
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
    backend_json_path = "/Backend_files/Config/" + backend_name + "/config.json"
    backend_config_dict = json.loads(
        storage_provider.get_file_content(storage_path=backend_json_path)
    )

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
    backend_config_dict["url"] = base_url + "/api/v1/" + backend_name + "/"

    return backend_config_dict


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


@api.get("/backends", response=List[BackendSchemaOut], tags=["Backend"])
def list_backends(request):
    """
    Returns the list of backends.
    """
    # pylint: disable=W0613, E1101
    backends = Backend.objects.all()
    backend_list = []
    for backend in backends:
        config_dict = {
            "conditional": False,
            "coupling_map": "linear",
            "dynamic_reprate_enabled": False,
            "local": False,
            "memory": True,
            "open_pulse": False,
        }
        config_dict["display_name"] = backend.name
        config_dict["description"] = backend.description
        config_dict["backend_version"] = backend.version
        config_dict["cold_atom_type"] = backend.cold_atom_type
        config_dict["simulator"] = backend.simulator
        config_dict["num_species"] = backend.num_species
        config_dict["max_shots"] = backend.max_shots
        config_dict["max_experiments"] = backend.max_experiments
        config_dict["n_qubits"] = backend.num_wires
        config_dict["supported_instructions"] = backend.supported_instructions
        config_dict["wire_order"] = backend.wire_order
        if backend.simulator:
            config_dict["backend_name"] = "synqs_" + backend.name + "_simulator"
        else:
            config_dict["backend_name"] = "synqs_" + backend.name + "_machine"
        config_dict["gates"] = backend.gates

        config_dict["basis_gates"] = []
        for gate in config_dict["gates"]:
            config_dict["basis_gates"].append(gate["name"])

        # it would be really good to remove the first part and replace it by the domain
        config_dict["url"] = (
            "https://coquma-sim.herokuapp.com/api/" + backend.name + "/"
        )

        backend_list.append(config_dict)
    return backend_list
