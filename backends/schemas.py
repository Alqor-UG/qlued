"""
The schemas that define our communication with the api_v1.
"""


from typing import List
from ninja import ModelSchema, Schema
from .models import Backend


# pylint: disable=R0903
class JobSchemaIn(Schema):
    """
    The schema that is set up for the submission of new jobs.  We follow the
    conventions of the `qiskit-cold-atom` here.
    """

    job: str
    username: str
    password: str


class JobResponseSchema(Schema):
    """
    The schema for any job response.
    """

    job_id: str
    status: str
    detail: str
    error_message: str


# pylint: disable=R0903
class BackendSchemaOut(ModelSchema):
    """
    The schema send out to detail the configuration of the backend. We follow the
    conventions of the qiskit configuration dictionary here
    """

    display_name: str
    conditional: bool = False
    coupling_map: str = "linear"
    dynamic_reprate_enabled: bool = False
    local: bool = False
    memory: bool = True
    open_pulse: bool = False
    backend_version: str
    n_qubits: int
    backend_name: str
    basis_gates: List[str]
    url: str

    # pylint: disable=C0115
    class Config:
        model = Backend
        model_fields = [
            "description",
            "cold_atom_type",
            "max_experiments",
            "max_shots",
            "simulator",
            "wire_order",
            "num_species",
            "gates",
            "supported_instructions",
        ]
