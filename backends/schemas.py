"""
The schemas that define our communication with the api.
"""


from typing import Optional, TypedDict
from ninja import Schema


class ResultDict(TypedDict):
    """
    A class that defines the structure of results.
    """

    display_name: str
    backend_name: str
    backend_version: str
    job_id: str
    qobj_id: Optional[str]
    success: bool
    status: str
    header: dict
    results: list


# pylint: disable=R0903
class JobSchemaIn(Schema):
    """
    The schema that is set up for the submission of new jobs.  We follow the
    conventions of the `qiskit-cold-atom` here.
    """

    job: str
    username: str
    password: str


# pylint: disable=R0903
class JobSchemaWithTokenIn(Schema):
    """
    The schema that is set up for the submission of new jobs.  This is the schema used in v2
    as it allows for token based authentification only.
    """

    job: str
    token: str


class JobResponseSchema(Schema):
    """
    The schema for any job response.
    """

    job_id: str
    status: str
    detail: str
    error_message: str
