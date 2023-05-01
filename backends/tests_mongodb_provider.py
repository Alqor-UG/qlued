"""
The tests for the storage provider
"""
import uuid

from django.test import TestCase
from .storage_providers import MongodbProvider


class MongodbProviderTest(TestCase):
    """
    The class that contains all the tests for the dropbox provider.
    """

    def setUp(self):
        """
        set up the test.
        """
        # load the credentials from the environment through decouple
        self.storage_provider = MongodbProvider()

    def test_upload_etc(self):
        """
        Test that it is possible to upload a file.
        """

        # upload a file and get it back
        test_content = {"experiment_0": "Nothing happened here."}
        storage_path = "test/subcollection"

        job_id = uuid.uuid4().hex[:24]
        self.storage_provider.upload(test_content, storage_path, job_id)
        test_result = self.storage_provider.get_file_content(storage_path, job_id)

        self.assertDictEqual(test_content, test_result)

        # move it and get it back
        second_path = "test/subcollection_2"
        self.storage_provider.move_file(storage_path, second_path, job_id)
        test_result = self.storage_provider.get_file_content(second_path, job_id)
        self.assertDictEqual(test_content, test_result)

        # clean up our mess
        self.storage_provider.delete_file(second_path, job_id)

    def test_configs(self):
        """
        Test that we are able to obtain a list of backends.
        """

        # create a dummy config
        dummy_id = uuid.uuid4().hex[:5]
        dummy_dict: dict = {}
        dummy_dict["gates"] = []
        dummy_dict["name"] = "Dummy"
        dummy_dict["num_wires"] = 3
        dummy_dict["version"] = "0.0.1"

        backend_name = f"dummy_{dummy_id}"
        dummy_dict["display_name"] = backend_name

        config_path = "Backend_files/Config"
        self.storage_provider.upload(
            dummy_dict, config_path, job_id=uuid.uuid4().hex[:24]
        )

        # can we get the backend in the list ?
        backends = self.storage_provider.get_backends()
        self.assertTrue(f"dummy_{dummy_id}" in backends)
