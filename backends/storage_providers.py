"""
The module that contains all the necessary logic for communication with the external
storage for the jobs.
"""
from abc import ABC
import sys
from typing import List
import json

import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError
from decouple import config


class StorageProvider(ABC):
    """
    The template for accessing any storage providers like dropbox, amazon S3 etc.
    """

    def upload(self, dump_str: str, storage_path: str) -> None:
        """
        Upload the file to the storage
        """

    def get_file_content(self, storage_path: str) -> str:
        """
        Get the file content from the storage
        """

    def get_file_queue(self, storage_path: str) -> List[str]:
        """
        Get a list of files
        """

    def move_file(self, start_path: str, final_path: str) -> None:
        """
        Move the file from start_path to `final_path`
        """

    def get_backends(self) -> List[str]:
        """
        Get a list of all the backends that the provider offers.
        """

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
    def __init__(self):
        """
        Set up the neccessary keys.
        """
        self.app_key = config("APP_KEY")
        self.app_secret = config("APP_SECRET")
        self.refresh_token = config("REFRESH_TOKEN")

    def upload(self, dump_str: str, storage_path: str) -> None:
        """
        Upload the file identified to the dropbox
        """
        # Create an instance of a Dropbox class, which can make requests to the API.
        with dropbox.Dropbox(
            app_key=self.app_key,
            app_secret=self.app_secret,
            oauth2_refresh_token=self.refresh_token,
        ) as dbx:
            # Check that the access token is valid
            dbx.users_get_current_account()
            dbx.files_upload(
                dump_str.encode("utf-8"), storage_path, mode=WriteMode("overwrite")
            )

    def get_file_content(self, storage_path: str) -> str:
        """
        Get the file content from the dropbox
        """
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
            # We should really handle these exceptions cleaner, but this seems a bit
            # complicated right now
            # pylint: disable=W0703
            try:
                _, res = dbx.files_download(path=storage_path)
                data = res.content
            except Exception as err:
                sys.exit(err)
        return data.decode("utf-8")

    def get_file_queue(self, storage_path: str) -> List[str]:
        """
        Get a list of files
        """

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
            # We should really handle these exceptions cleaner, but this seems a bit
            # complicated right now
            # pylint: disable=W0703
            try:
                response = dbx.files_list_folder(path=storage_path)
                file_list = response.entries
                file_list = [item.name for item in file_list]

            except Exception as err:
                print(err)
        return file_list

    def move_file(self, start_path: str, final_path: str) -> None:
        """
        Move the file from start_path to
        """

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
            try:
                dbx.files_move_v2(start_path, final_path)
            except ApiError as err:
                print(err)
                sys.exit()

    def delete_file(self, storage_path: str):
        """
        Remove the file from the dropbox
        """
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
            # We should really handle these exceptions cleaner, but this seems a bit
            # complicated right now
            # pylint: disable=W0703
            try:
                _ = dbx.files_delete(path=storage_path)
            except Exception as err:
                sys.exit(err)

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
            # We should really handle these exceptions cleaner, but this seems a bit
            # complicated right now
            # pylint: disable=W0703
            try:
                folders_results = dbx.files_list_folder(path=backend_config_path)
                entries = folders_results.entries
                backend_names = []
                for entry in entries:
                    backend_names.append(entry.name)
            except Exception as err:
                sys.exit(err)
        return backend_names

    def get_backend_dict(self, backend_name: str, version: str = "v2") -> dict:
        """
        The configuration of the backend.

        Args:
            backend_name: The identifier of the backend

        Returns:
            The full schema of the backend.
        """
        backend_json_path = "/Backend_files/Config/" + backend_name + "/config.json"
        backend_config_dict = json.loads(
            self.get_file_content(storage_path=backend_json_path)
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

    def upload(self, content_dict: dict, storage_path: str, file_id: str) -> None:
        """
        Upload the file to the storage

        content_dict: the content that should be uploaded onto the mongodb base
        storage_path: the access path towards the mongodb collection
        file_id: the id of the file we are about to create
        """

    def get_file_content(self, storage_path: str) -> str:
        """
        Get the file content from the storage

        storage_path: the path towards the file, excluding the filename / id
        file_id: the id of the file we are about to look up
        """

    def get_file_queue(self, storage_path: str) -> List[str]:
        """
        Get a list of files
        """

    def move_file(self, start_path: str, final_path: str) -> None:
        """
        Move the file from start_path to `final_path`

        storage_path: the access path at which we start (excluding the file id)
        final_path: the access path at which we put the file (excluding the file id)
        file_id: the id of the file we are about to move
        """

    def get_backends(self) -> List[str]:
        """
        Get a list of all the backends that the provider offers.
        """

    def get_backend_dict(self, backend_name: str, version: str) -> dict:
        """
        The configuration of the backend.

        Args:
            backend_name: The identifier of the backend
            version: the version of the API you are using

        Returns:
            The full schema of the backend.
        """