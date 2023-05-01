"""
The module that contains all the necessary logic for communication with the external
storage for the jobs.
"""
from abc import ABC, abstractmethod
import sys
from typing import List
import json

# necessary for the dropbox provider
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import AuthError

# necessary for the mongodb provider
from pymongo.mongo_client import MongoClient
from bson.objectid import ObjectId

# get the environment variables
from decouple import config


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


class DropboxProvider(StorageProvider):
    """
    The access to the dropbox
    """

    # Add OAuth2 access token here.
    # You can generate one for yourself in the App Console.
    # <https://blogs.dropbox.com/developers/2014/05/generate-an-access-token-for-your-own-account/>
    def __init__(self) -> None:
        """
        Set up the neccessary keys.
        """
        self.app_key = config("APP_KEY")
        self.app_secret = config("APP_SECRET")
        self.refresh_token = config("REFRESH_TOKEN")

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


class MongodbProvider(StorageProvider):
    """
    The access to the mongodb
    """

    def __init__(self) -> None:
        """
        Set up the neccessary keys and create the client through which all the connections will run.
        """
        mongodb_username = config("MONGODB_USERNAME")
        mongodb_password = config("MONGODB_PASSWORD")
        mongodb_database_url = config("MONGODB_DATABASE_URL")

        uri = f"mongodb+srv://{mongodb_username}:{mongodb_password}@{mongodb_database_url}/?retryWrites=true&w=majority"
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
        for config in config_collection.find():
            backend_names.append(config["display_name"])
        return backend_names

    def get_backend_dict(self, backend_name: str, version: str) -> dict:
        """
        The configuration of the backend.

        Args:
            backend_name: The identifier of the backend
            version: the version of the API you are using

        Returns:
            The full schema of the backend.
        """
