"""
Module that defines the user api v1 which goes through django-ninja.
"""

import json
from typing import List
from ninja import NinjaAPI

from decouple import config

from .schemas import BackendSchemaOut
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
    backend_config_dict["url"] = base_url + "/api/" + backend_name + "/"

    return backend_config_dict


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
