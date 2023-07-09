"""
The module that contains all the necessary logic for communication with the external
storage for the jobs.
"""
from abc import ABC, abstractmethod
import sys
from typing import List
import json

# necessary for the dropbox provider
import datetime
import uuid

import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import AuthError

# necessary for the mongodb provider
from pymongo.mongo_client import MongoClient
from bson.objectid import ObjectId

# get the environment variables
from decouple import config
from pydantic import BaseModel


class StorageProvider(ABC):
    """
    The template for accessing any storage providers like dropbox, amazon S3 etc.
    """

    @abstractmethod
    def upload(self, content_dict: dict, storage_path: str, job_id: str) -> None:
        """
        Upload the file to the storage
        """

    @abstractmethod
    def get_file_content(self, storage_path: str, job_id: str) -> dict:
        """
        Get the file content from the storage
        """

    @abstractmethod
    def move_file(self, start_path: str, final_path: str, job_id: str) -> None:
        """
        Move the file from `start_path` to `final_path`
        """

    @abstractmethod
    def get_backends(self) -> List[str]:
        """
        Get a list of all the backends that the provider offers.
        """

    @abstractmethod
    def get_backend_dict(self, backend_name: str, version: str) -> dict:
        """
        The configuration of the backend.

        Args:
            backend_name: The identifier of the backend
            version: the version of the API you are using

        Returns:
            The full schema of the backend.
        """

    @abstractmethod
    def upload_job(self, job_dict: dict, backend_name: str, username: str) -> str:
        """
        Upload the job to the storage provider.

        Args:
            job_dict: the full job dict
            backend_name: the name of the backend
            username: the name of the user that submitted the job

        Returns:
            The job id of the uploaded job.
        """

    @abstractmethod
    def upload_status(self, backend_name: str, username: str, job_id: str) -> dict:
        """
        This function uploads a status file to the backend and creates the status dict.

        Args:
            backend_name: The name of the backend to which we want to upload the job
            username: The username of the user that is uploading the job
            job_id: The job_id of the job that we want to upload the status for

        Returns:
            The status dict of the job
        """

    @abstractmethod
    def get_status(self, backend_name: str, username: str, job_id: str) -> dict:
        """
        This function gets the status file from the backend and returns the status dict.

        Args:
            backend_name: The name of the backend to which we want to upload the job
            username: The username of the user that is uploading the job
            job_id: The job_id of the job that we want to upload the status for

        Returns:
            The status dict of the job
        """

    @abstractmethod
    def get_result(self, backend_name: str, username: str, job_id: str) -> dict:
        """
        This function gets the result file from the backend and returns the result dict.

        Args:
            backend_name: The name of the backend to which we want to upload the job
            username: The username of the user that is uploading the job
            job_id: The job_id of the job that we want to upload the status for

        Returns:
            The result dict of the job
        """


class DropboxLoginInformation(BaseModel):
    """
    The login information for the dropbox
    """

    app_key: str
    app_secret: str
    refresh_token: str


class DropboxProvider(StorageProvider):
    """
    The access to the dropbox. <https://blogs.dropbox.com/developers/2014/05/generate-an-access-token-for-your-own-account/>
    """

    def __init__(self, login_dict: dict) -> None:
        """
        Set up the neccessary keys.

        Args:
            login_dict: The dictionary that contains the login information

        Raises:
            ValidationError: If the login_dict does not contain the correct keys
        """
        DropboxLoginInformation(**login_dict)

        self.app_key = login_dict["app_key"]
        self.app_secret = login_dict["app_secret"]
        self.refresh_token = login_dict["refresh_token"]

    def upload(self, content_dict: dict, storage_path: str, job_id: str) -> None:
        """
        Upload the content_dict as a json file to the dropbox

        content_dict: the content of the file that should be uploaded
        storage_path: the path where the file should be stored, but excluding the file name
        job_id: the name of the file without the .json extension
        """

        # create the appropriate string for the dropbox API
        dump_str = json.dumps(content_dict)

        # strip trailing and leading slashes from the storage_path
        storage_path = storage_path.strip("/")

        # create the full path
        full_path = "/" + storage_path + "/" + job_id + ".json"

        # Create an instance of a Dropbox class, which can make requests to the API.
        with dropbox.Dropbox(
            app_key=self.app_key,
            app_secret=self.app_secret,
            oauth2_refresh_token=self.refresh_token,
        ) as dbx:
            # Check that the access token is valid
            dbx.users_get_current_account()
            dbx.files_upload(
                dump_str.encode("utf-8"), full_path, mode=WriteMode("overwrite")
            )

    def get_file_content(self, storage_path: str, job_id: str) -> dict:
        """
        Get the file content from the dropbox

        storage_path: the path where the file should be stored, but excluding the file name
        job_id: the name of the file. Is a json file
        """

        # strip trailing and leading slashes from the storage_path
        storage_path = storage_path.strip("/")

        # Create an instance of a Dropbox class, which can make requests to the API.
        with dropbox.Dropbox(
            app_key=self.app_key,
            app_secret=self.app_secret,
            oauth2_refresh_token=self.refresh_token,
        ) as dbx:
            # Check that the access token is valid
            try:
                dbx.users_get_current_account()
            except AuthError:
                sys.exit("ERROR: Invalid access token.")
            full_path = "/" + storage_path + "/" + job_id + ".json"
            _, res = dbx.files_download(path=full_path)
            data = res.content
        return json.loads(data.decode("utf-8"))

    def move_file(self, start_path: str, final_path: str, job_id: str) -> None:
        """
        Move the file from start_path to final_path

        start_path: the path where the file is currently stored, but excluding the file name
        final_path: the path where the file should be stored, but excluding the file name
        job_id: the name of the file. Is a json file

        Returns:
            None
        """
        # strip trailing and leading slashes from the paths
        start_path = start_path.strip("/")
        final_path = final_path.strip("/")

        # Create an instance of a Dropbox class, which can make requests to the API.
        with dropbox.Dropbox(
            app_key=self.app_key,
            app_secret=self.app_secret,
            oauth2_refresh_token=self.refresh_token,
        ) as dbx:
            # Check that the access token is valid
            try:
                dbx.users_get_current_account()
            except AuthError:
                sys.exit("ERROR: Invalid access token.")

            full_start_path = "/" + start_path + "/" + job_id + ".json"
            full_final_path = "/" + final_path + "/" + job_id + ".json"
            dbx.files_move_v2(full_start_path, full_final_path)

    def delete_file(self, storage_path: str, job_id: str) -> None:
        """
        Remove the file from the dropbox
        """

        # strip trailing and leading slashes from the storage_path
        storage_path = storage_path.strip("/")

        # Create an instance of a Dropbox class, which can make requests to the API.
        with dropbox.Dropbox(
            app_key=self.app_key,
            app_secret=self.app_secret,
            oauth2_refresh_token=self.refresh_token,
        ) as dbx:
            # Check that the access token is valid
            try:
                dbx.users_get_current_account()
            except AuthError:
                sys.exit("ERROR: Invalid access token.")

            full_path = "/" + storage_path + "/" + job_id + ".json"
            _ = dbx.files_delete(path=full_path)

    def get_backends(self) -> List[str]:
        """
        Get a list of all the backends that the provider offers.
        """
        backend_config_path = "/Backend_files/Config/"
        with dropbox.Dropbox(
            app_key=self.app_key,
            app_secret=self.app_secret,
            oauth2_refresh_token=self.refresh_token,
        ) as dbx:
            # Check that the access token is valid
            try:
                dbx.users_get_current_account()
            except AuthError:
                sys.exit("ERROR: Invalid access token.")

            folders_results = dbx.files_list_folder(path=backend_config_path)
            entries = folders_results.entries
            backend_names = []
            for entry in entries:
                backend_names.append(entry.name)
        return backend_names

    def get_backend_dict(self, backend_name: str, version: str = "v2") -> dict:
        """
        The configuration of the backend.

        Args:
            backend_name: The identifier of the backend

        Returns:
            The full schema of the backend.
        """
        backend_json_path = f"Backend_files/Config/{backend_name}"
        backend_config_dict = self.get_file_content(
            storage_path=backend_json_path, job_id="config"
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
        backend_config_dict["url"] = base_url + f"/api/{version}/" + backend_name + "/"
        return backend_config_dict

    def upload_job(self, job_dict: dict, backend_name: str, username: str) -> str:
        """
        This function uploads a job to the backend and creates the job_id.

        Args:
            job_dict: The job dictionary that should be uploaded
            backend_name: The name of the backend to which we want to upload the job
            username: The username of the user that is uploading the job

        Returns:
            The job_id of the uploaded job
        """
        job_id = (
            (datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S"))
            + "-"
            + backend_name
            + "-"
            + username
            + "-"
            + (uuid.uuid4().hex)[:5]
        )
        # now we upload the job to the backend
        # this is currently very much backend specific
        job_json_dir = "/Backend_files/Queued_Jobs/" + backend_name + "/"
        job_json_name = "job-" + job_id

        self.upload(
            content_dict=job_dict, storage_path=job_json_dir, job_id=job_json_name
        )
        return job_id

    def upload_status(self, backend_name: str, username: str, job_id: str) -> dict:
        """
        This function uploads a status file to the backend and creates the status dict.

        Args:
            backend_name: The name of the backend to which we want to upload the job
            username: The username of the user that is uploading the job
            job_id: The job_id of the job that we want to upload the status for

        Returns:
            The status dict of the job
        """
        status_json_dir = "Backend_files/Status/" + backend_name + "/" + username
        status_json_name = "status-" + job_id
        status_dict = {
            "job_id": job_id,
            "status": "INITIALIZING",
            "detail": "Got your json.",
            "error_message": "None",
        }
        self.upload(
            content_dict=status_dict,
            storage_path=status_json_dir,
            job_id=status_json_name,
        )
        return status_dict

    def get_status(self, backend_name: str, username: str, job_id: str) -> dict:
        """
        This function gets the status file from the backend and returns the status dict.

        Args:
            backend_name: The name of the backend to which we want to upload the job
            username: The username of the user that is uploading the job
            job_id: The job_id of the job that we want to upload the status for

        Returns:
            The status dict of the job
        """
        status_json_dir = "Backend_files/Status/" + backend_name + "/" + username
        status_json_name = "status-" + job_id

        status_dict = self.get_file_content(
            storage_path=status_json_dir, job_id=status_json_name
        )
        return status_dict

    def get_result(self, backend_name: str, username: str, job_id: str) -> dict:
        """
        This function gets the result file from the backend and returns the result dict.

        Args:
            backend_name: The name of the backend to which we want to upload the job
            username: The username of the user that is uploading the job
            job_id: The job_id of the job that we want to upload the status for

        Returns:
            The result dict of the job
        """
        result_json_dir = "Backend_files/Result/" + backend_name + "/" + username
        result_json_name = "result-" + job_id
        result_dict = self.get_file_content(
            storage_path=result_json_dir, job_id=result_json_name
        )
        return result_dict


class MongodbLoginInformation(BaseModel):
    """
    The login information for MongoDB
    """

    mongodb_username: str
    mongodb_password: str
    mongodb_database_url: str


class MongodbProvider(StorageProvider):
    """
    The access to the mongodb
    """

    def __init__(self, login_dict: dict) -> None:
        """
        Set up the neccessary keys and create the client through which all the connections will run.

        Args:
            login_dict: The login dict that contains the neccessary information to connect to the mongodb

        Raises:
            ValidationError: If the login_dict is not valid
        """
        MongodbLoginInformation(**login_dict)
        mongodb_username = login_dict["mongodb_username"]
        mongodb_password = login_dict["mongodb_password"]
        mongodb_database_url = login_dict["mongodb_database_url"]

        uri = f"mongodb+srv://{mongodb_username}:{mongodb_password}@{mongodb_database_url}"
        uri = uri + "/?retryWrites=true&w=majority"
        # Create a new client and connect to the server
        self.client: MongoClient = MongoClient(uri)

        # Send a ping to confirm a successful connection
        self.client.admin.command("ping")

    def upload(self, content_dict: dict, storage_path: str, job_id: str) -> None:
        """
        Upload the file to the storage

        content_dict: the content that should be uploaded onto the mongodb base
        storage_path: the access path towards the mongodb collection
        job_id: the id of the file we are about to create
        """
        storage_splitted = storage_path.split("/")

        # get the database on which we work
        database = self.client[storage_splitted[0]]

        # get the collection on which we work
        collection_name = ".".join(storage_splitted[1:])
        collection = database[collection_name]

        content_dict["_id"] = ObjectId(job_id)
        collection.insert_one(content_dict)

        # remove the id from the content dict for further use
        content_dict.pop("_id", None)

    def get_file_content(self, storage_path: str, job_id: str) -> dict:
        """
        Get the file content from the storage

        storage_path: the path towards the file, excluding the filename / id
        job_id: the id of the file we are about to look up
        """
        document_to_find = {"_id": ObjectId(job_id)}

        # get the database on which we work
        database = self.client[storage_path.split("/")[0]]

        # get the collection on which we work
        collection_name = ".".join(storage_path.split("/")[1:])
        collection = database[collection_name]

        result_found = collection.find_one(document_to_find)

        if not result_found:
            return {}

        # remove the id from the result dict for further use
        result_found.pop("_id", None)
        return result_found

    def move_file(self, start_path: str, final_path: str, job_id: str) -> None:
        """
        Move the file from start_path to final_path

        start_path: the path where the file is currently stored, but excluding the file name
        final_path: the path where the file should be stored, but excluding the file name
        job_id: the name of the file. Is a json file

        Returns:
            None
        """
        # get the database on which we work
        database = self.client[start_path.split("/")[0]]

        # get the collection on which we work
        collection_name = ".".join(start_path.split("/")[1:])
        collection = database[collection_name]

        document_to_find = {"_id": ObjectId(job_id)}
        result_found = collection.find_one(document_to_find)

        # delete the old file
        collection.delete_one(document_to_find)

        # add the document to the new collection
        database = self.client[final_path.split("/")[0]]
        collection_name = ".".join(final_path.split("/")[1:])
        collection = database[collection_name]
        collection.insert_one(result_found)

    def delete_file(self, storage_path: str, job_id: str) -> None:
        """
        Remove the file from the mongodb database

        Args:
            storage_path: the path where the file is currently stored, but excluding the file name
            job_id: the name of the file

        Returns:
            None
        """
        # get the database on which we work
        database = self.client[storage_path.split("/")[0]]

        # get the collection on which we work
        collection_name = ".".join(storage_path.split("/")[1:])
        collection = database[collection_name]

        document_to_find = {"_id": ObjectId(job_id)}
        collection.delete_one(document_to_find)

    def get_backends(self) -> List[str]:
        """
        Get a list of all the backends that the provider offers.
        """

        # get the database on which we work
        database = self.client["backends"]
        config_collection = database["configs"]
        # get all the documents in the collection configs and save the disply_name in a list
        backend_names: list[str] = []
        for config_dict in config_collection.find():
            backend_names.append(config_dict["display_name"])
        return backend_names

    def get_backend_dict(self, backend_name: str, version: str = "v2") -> dict:
        """
        The configuration dictionary of the backend such that it can be sent out to the API to
        the common user. We make sure that it is compatible with QISKIT within this function.

        Args:
            backend_name: The identifier of the backend
            version: the version of the API you are using

        Returns:
            The full schema of the backend.
        """
        # get the database on which we work
        database = self.client["backends"]
        config_collection = database["configs"]

        # create the filter for the document with display_name that is equal to backend_name
        document_to_find = {"display_name": backend_name}
        backend_config_dict = config_collection.find_one(document_to_find)

        if not backend_config_dict:
            return {}

        backend_config_dict.pop("_id")
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
        backend_config_dict["url"] = f"{base_url}/api/{version}/{backend_name}/"
        return backend_config_dict

    def upload_job(self, job_dict: dict, backend_name: str, username: str) -> str:
        """
        Upload the job to the storage provider.

        Args:
            job_dict: the full job dict
            backend_name: the name of the backend
            username: the name of the user that submitted the job

        Returns:
            The job id of the uploaded job.
        """

        storage_path = "jobs/queued/" + backend_name
        job_id = (uuid.uuid4().hex)[:24]

        self.upload(content_dict=job_dict, storage_path=storage_path, job_id=job_id)
        return job_id

    def upload_status(self, backend_name: str, username: str, job_id: str) -> dict:
        """
        This function uploads a status file to the backend and creates the status dict.

        Args:
            backend_name: The name of the backend to which we want to upload the job
            username: The username of the user that is uploading the job
            job_id: The job_id of the job that we want to upload the status for

        Returns:
            The status dict of the job
        """
        storage_path = "status/" + backend_name
        status_dict = {
            "job_id": job_id,
            "status": "INITIALIZING",
            "detail": "Got your json.",
            "error_message": "None",
        }

        # should we also upload the username into the dict ?

        # now upload the status dict
        self.upload(
            content_dict=status_dict,
            storage_path=storage_path,
            job_id=job_id,
        )
        return status_dict

    def get_status(self, backend_name: str, username: str, job_id: str) -> dict:
        """
        This function gets the status file from the backend and returns the status dict.

        Args:
            backend_name: The name of the backend to which we want to upload the job
            username: The username of the user that is uploading the job
            job_id: The job_id of the job that we want to upload the status for

        Returns:
            The status dict of the job
        """
        status_json_dir = "status/" + backend_name

        status_dict = self.get_file_content(storage_path=status_json_dir, job_id=job_id)
        return status_dict

    def get_result(self, backend_name: str, username: str, job_id: str) -> dict:
        """
        This function gets the result file from the backend and returns the result dict.

        Args:
            backend_name: The name of the backend to which we want to upload the job
            username: The username of the user that is uploading the job
            job_id: The job_id of the job that we want to upload the status for

        Returns:
            The result dict of the job
        """
        result_json_dir = "results/" + backend_name
        result_dict = self.get_file_content(storage_path=result_json_dir, job_id=job_id)
        return result_dict


def get_storage_provider(backend_name: str) -> StorageProvider:
    """
    Get the storage provider that is used for the backend.

    Args:
        backend_name: The name of the backend

    Returns:
        The storage provider that is used for the backend

    Raises:
        ValueError: If the storage provider is not supported
    """

    # we have to import it here to avoid circular imports
    from .models import StorageProviderDb

    # we often identify the backend by its short name. Let us use the assumption that this means that we
    # work with a default database. This is part of bug #152
    if len(backend_name.split("_")) == 1:
        # we should change this default name to something more sensible in the config file
        # TODO: change the default name to something more sensible
        storage_provider_name = "alqor"
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

    if storage_provider_entry.storage_type == "mongodb":
        return MongodbProvider(storage_provider_entry.login)
    elif storage_provider_entry.storage_type == "dropbox":
        return DropboxProvider(storage_provider_entry.login)
    raise ValueError("The storage provider is not supported.")
