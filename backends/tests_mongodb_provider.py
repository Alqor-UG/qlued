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

        config_path = "backends/configs"
        mongo_id = uuid.uuid4().hex[:24]
        self.storage_provider.upload(dummy_dict, config_path, job_id=mongo_id)

        # can we get the backend in the list ?
        backends = self.storage_provider.get_backends()
        self.assertTrue(f"dummy_{dummy_id}" in backends)

        # can we get the config of the backend ?
        backend_dict = self.storage_provider.get_backend_dict(backend_name)
        self.assertEqual(backend_dict["backend_name"], dummy_dict["name"])
        self.storage_provider.delete_file(config_path, mongo_id)

    def test_jobs(self):
        """
        Test that we can handle the necessary functions for the jobs and status.
        """
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

        job_id = self.storage_provider.upload_job(
            job_dict=job_payload, backend_name=backend_name, username=username
        )
        self.assertTrue(len(job_id) > 1)

        # now also test that we can upload the status
        job_response_dict = self.storage_provider.upload_status(
            backend_name=backend_name,
            username=username,
            job_id=job_id,
        )
        self.assertTrue(len(job_response_dict["job_id"]) > 1)
        # now test that we can get the job status
        job_status = self.storage_provider.get_status(
            backend_name=backend_name,
            username=username,
            job_id=job_id,
        )
        self.assertFalse("_id" in job_status.keys())
        self.assertEqual(job_status["job_id"], job_id)

        # test that we can get a job result
        # first upload a dummy result
        dummy_result = {"result": "dummy"}
        result_json_dir = "results/" + backend_name
        self.storage_provider.upload(dummy_result, result_json_dir, job_id)

        # now get the result
        result = self.storage_provider.get_result(
            backend_name=backend_name,
            username=username,
            job_id=job_id,
        )
        self.assertFalse("_id" in result.keys())
        self.assertEqual(dummy_result["result"], result["result"])

        # remove the obsolete job from the storage
        job_dir = "jobs/queued/" + backend_name
        self.storage_provider.delete_file(job_dir, job_id)

        # remove the obsolete status from the storage
        status_dir = "status/" + backend_name
        self.storage_provider.delete_file(status_dir, job_id)

        # remove the obsolete result from the storage
        self.storage_provider.delete_file(result_json_dir, job_id)
