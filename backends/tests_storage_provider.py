"""
The tests for the storage provider
"""
import json
import uuid

from django.test import TestCase
from .apps import BackendsConfig as ac


class DropboxProvideTest(TestCase):
    """
    The class that contains all the tests for the dropbox provider.
    """

    def setUp(self):
        """
        set up the test.
        """
        self.storage_provider = getattr(ac, "storage")

    def test_upload_etc(self):
        """
        Test that it is possible to upload a file.
        """

        # upload a file and get it back
        file_id = uuid.uuid4().hex
        dump_str = "Hello world"
        self.storage_provider.upload(dump_str, f"/test_folder/world-{file_id}.txt")
        world_str = self.storage_provider.get_file_content(
            f"/test_folder/world-{file_id}.txt"
        )
        self.assertEqual("Hello world", world_str)

        # move it and get it back
        self.storage_provider.move_file(
            f"/test_folder/world-{file_id}.txt",
            f"/test_folder/copied_world-{file_id}.txt",
        )
        world_str = self.storage_provider.get_file_content(
            f"/test_folder/copied_world-{file_id}.txt"
        )
        self.assertEqual("Hello world", world_str)
        # this is not really meaningful to be
        file_list = self.storage_provider.get_file_queue("/test_folder/")
        self.assertTrue(len(file_list))

        # clean up our mess
        self.storage_provider.delete_file(f"/test_folder/copied_world-{file_id}.txt")

    def test_configs(self):
        """
        Test that we are able to obtain a list of backends.
        """

        # create a dummy config
        dummy_id = uuid.uuid4().hex[:5]
        dummy_dict = {}
        dummy_dict["gates"] = []
        dummy_dict["name"] = "Dummy"
        dummy_dict["num_wires"] = 3
        dummy_dict["version"] = "0.0.1"

        backend_name = f"dummy_{dummy_id}"
        dummy_f_name = f"/Backend_files/Config/{backend_name}/config.json"
        self.storage_provider.upload(json.dumps(dummy_dict), dummy_f_name)

        # can we get the backend in the list ?
        backends = self.storage_provider.get_backends()
        self.assertTrue(f"dummy_{dummy_id}" in backends)

        # can we get the config of the backend ?
        backend_dict = self.storage_provider.get_backend_dict(backend_name)
        self.assertEqual(backend_dict["backend_name"], dummy_dict["name"])
        self.storage_provider.delete_file(f"/Backend_files/Config/{backend_name}")
