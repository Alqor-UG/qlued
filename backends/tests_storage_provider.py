"""
The tests for the storage provider
"""

import uuid
from pydantic import ValidationError
from decouple import config

from django.test import TestCase
from django.contrib.auth import get_user_model


from .models import StorageProviderDb
from .storage_providers import DropboxProvider

User = get_user_model()


class DropboxProvideTest(TestCase):
    """
    The class that contains all the tests for the dropbox provider.
    """

    def setUp(self):
        """
        set up the test.
        """

        # create a user
        self.username = config("USERNAME_TEST")
        self.password = config("PASSWORD_TEST")
        user = User.objects.create(username=self.username)
        user.set_password(self.password)
        user.save()
        self.user = user

        # put together the login information
        app_key = config("APP_KEY")
        app_secret = config("APP_SECRET")
        refresh_token = config("REFRESH_TOKEN")

        login_dict = {
            "app_key": app_key,
            "app_secret": app_secret,
            "refresh_token": refresh_token,
        }

        # create the storage entry in the models
        dropbox_entry = StorageProviderDb.objects.create(
            storage_type="dropbox",
            name="dropboxtest",
            owner=self.user,
            description="Dropbox storage provider for tests",
            login=login_dict,
        )
        dropbox_entry.full_clean()
        dropbox_entry.save()

    def test_dropbox_object(self):
        """
        Test that we can create a dropbox object.
        """
        dropbox_entry = StorageProviderDb.objects.get(name="dropboxtest")
        dropbox_provider = DropboxProvider(dropbox_entry.login, dropbox_entry.name)
        self.assertIsNotNone(dropbox_provider)

        # test that we cannot create a dropbox object a poor login dict structure
        poor_login_dict = {
            "app_key_t": "test",
            "app_secret": "test",
            "refresh_token": "test",
        }
        with self.assertRaises(ValidationError):
            DropboxProvider(poor_login_dict, dropbox_entry.name)

    def test_upload_etc(self):
        """
        Test that it is possible to upload a file.
        """

        # create a dropbox object
        dropbox_entry = StorageProviderDb.objects.get(name="dropboxtest")
        storage_provider = DropboxProvider(dropbox_entry.login, dropbox_entry.name)

        # upload a file and get it back
        file_id = uuid.uuid4().hex
        test_content = {"experiment_0": "Nothing happened here."}
        storage_path = "test_folder"
        job_id = f"world-{file_id}"
        storage_provider.upload(test_content, storage_path, job_id)

        # make sure that this did not add the _id field to the dict
        self.assertFalse("_id" in test_content)

        test_result = storage_provider.get_file_content(storage_path, job_id)

        self.assertDictEqual(test_content, test_result)

        # move it and get it back
        second_path = "test_folder_2"
        storage_provider.move_file(storage_path, second_path, job_id)
        test_result = storage_provider.get_file_content(second_path, job_id)
        self.assertDictEqual(test_content, test_result)

        # clean up our mess
        storage_provider.delete_file(second_path, job_id)

    def test_configs(self):
        """
        Test that we are able to obtain a list of backends.
        """

        # create a dropbox object
        dropbox_entry = StorageProviderDb.objects.get(name="dropboxtest")
        storage_provider = DropboxProvider(dropbox_entry.login, dropbox_entry.name)

        # create a dummy config
        dummy_id = uuid.uuid4().hex[:5]
        dummy_dict: dict = {}
        dummy_dict["gates"] = []
        dummy_dict["name"] = "Dummy"
        dummy_dict["num_wires"] = 3
        dummy_dict["version"] = "0.0.1"

        backend_name = f"dummy_{dummy_id}"
        dummy_path = f"Backend_files/Config/{backend_name}"
        storage_provider.upload(dummy_dict, dummy_path, job_id="config")

        # can we get the backend in the list ?
        backends = storage_provider.get_backends()
        self.assertTrue(f"dummy_{dummy_id}" in backends)

        # can we get the config of the backend ?
        backend_dict = storage_provider.get_backend_dict(backend_name)
        self.assertEqual(backend_dict["backend_name"], dummy_dict["name"])
        storage_provider.delete_file(dummy_path, "config")

    def test_jobs(self):
        """
        Test that we can handle the necessary functions for the jobs and status.
        """
        # pylint: disable=too-many-locals
        # create a dropbox object
        dropbox_entry = StorageProviderDb.objects.get(name="dropboxtest")
        storage_provider = DropboxProvider(dropbox_entry.login, dropbox_entry.name)

        # let us first test the we can upload a dummy job
        job_payload = {
            "experiment_0": {
                "instructions": [
                    ("load", [7], []),
                    ("load", [2], []),
                    ("measure", [2], []),
                    ("measure", [6], []),
                    ("measure", [7], []),
                ],
                "num_wires": 8,
                "shots": 4,
                "wire_order": "sequential",
            },
        }
        backend_name = "dummy" + uuid.uuid4().hex[:5]
        username = "dummy_user"

        job_id = storage_provider.upload_job(
            job_dict=job_payload, backend_name=backend_name, username=username
        )
        self.assertTrue(len(job_id) > 1)

        # now also test that we can upload the status
        job_response_dict = storage_provider.upload_status(
            backend_name=backend_name,
            username=username,
            job_id=job_id,
        )
        self.assertTrue(len(job_response_dict["job_id"]) > 1)

        # now test that we can get the job status
        job_status = storage_provider.get_status(
            backend_name=backend_name,
            username=username,
            job_id=job_id,
        )
        self.assertEqual(job_status["job_id"], job_id)

        # test that we can get a job result
        # first upload a dummy result
        dummy_result = {"result": "dummy"}
        result_json_dir = "Backend_files/Result/" + backend_name + "/" + username
        result_json_name = "result-" + job_id

        storage_provider.upload(dummy_result, result_json_dir, result_json_name)
        # now get the result
        result = storage_provider.get_result(
            backend_name=backend_name,
            username=username,
            job_id=job_id,
        )
        self.assertDictEqual(result, dummy_result)

        # remove the obsolete job from the storage folder on the dropbox
        job_dir = "/Backend_files/Queued_Jobs/" + backend_name + "/"
        job_name = "job-" + job_id
        storage_provider.delete_file(job_dir, job_name)

        # remove the obsolete status from the storage folder on the dropbox
        status_dir = "/Backend_files/Status/" + backend_name + "/" + username
        status_name = "status-" + job_id
        storage_provider.delete_file(status_dir, status_name)

        # remove the obsolete result from the storage folder on the dropbox
        storage_provider.delete_file(result_json_dir, result_json_name)
