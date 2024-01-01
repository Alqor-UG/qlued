"""
The tests for the storage provider
"""

import uuid
from pydantic import ValidationError
from decouple import config

from django.test import TestCase
from django.contrib.auth import get_user_model

from sqooler.storage_providers import DropboxProviderExtended as DropboxProvider
from sqooler.schemes import DropboxLoginInformation

from ..models import StorageProviderDb

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
        login_info = DropboxLoginInformation(**dropbox_entry.login)
        dropbox_provider = DropboxProvider(login_info, dropbox_entry.name)
        self.assertIsNotNone(dropbox_provider)

        # test that we cannot create a dropbox object a poor login dict structure
        poor_login_dict = {
            "app_key_t": "test",
            "app_secret": "test",
            "refresh_token": "test",
        }
        with self.assertRaises(ValidationError):
            login_info = DropboxLoginInformation(**poor_login_dict)
            DropboxProvider(login_info, dropbox_entry.name)

    def test_upload_etc(self):
        """
        Test that it is possible to upload a file.
        """

        # create a dropbox object
        dropbox_entry = StorageProviderDb.objects.get(name="dropboxtest")
        login_info = DropboxLoginInformation(**dropbox_entry.login)
        storage_provider = DropboxProvider(login_info, dropbox_entry.name)

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
