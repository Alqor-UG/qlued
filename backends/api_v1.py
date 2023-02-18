"""
Module that defines the user api v1 which goes through django-ninja.
"""
from typing import List, Tuple
from ninja import NinjaAPI
from django.contrib.auth import authenticate

from .schemas import BackendSchemaOut, JobSchemaIn, JobResponseSchema
from .models import Backend
from .apps import BackendsConfig as ac

api = NinjaAPI(version="1.0.0")


@api.get("{backend_name}/get_config", response=BackendSchemaOut, tags=["Backend"])
def get_config(request, backend_name: str):
    """
    Returns the list of backends.
    """
    # pylint: disable=W0613, E1101
    backend = Backend.objects.get(name=backend_name)
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
    config_dict["url"] = "https://coquma-sim.herokuapp.com/api/" + backend.name + "/"
    return config_dict


@api.get("{backend_name}/post_job", response= JobResponseSchema, tags=["Backend"], url_name="post_job")
def post_job(request, data: JobSchemaIn, backend_name: str):
    """
    A view to submit the job to the backend.

    Args:
        request: The request coming in
        backend_name (str): The name of the backend for the configuration should
            be obtained

    Returns:
        JsonResponse : send back a response with the dict if successful
    """

    job_response_dict = {
        "job_id": "None",
        "status": "None",
        "detail": "None",
        "error_message": "None",
    }

    username = data["username"]
    password = data["password"]
    
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
