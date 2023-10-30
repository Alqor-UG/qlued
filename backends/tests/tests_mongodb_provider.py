"""
The tests for the mongodb storage provider
"""
import uuid

from decouple import config
from pydantic import ValidationError

from django.contrib.auth import get_user_model
from django.test import TestCase

from ..storage_providers import MongodbProvider, get_short_backend_name
from ..models import StorageProviderDb

User = get_user_model()


class MongodbProviderTest(TestCase):
    """
    The class that contains all the tests for the dropbox provider.
    """

    def setUp(self):
        """
        set up the test.
        """
        # load the credentials from the environment through decouple

        # create a user
        self.username = config("USERNAME_TEST")
        self.password = config("PASSWORD_TEST")
        user = User.objects.create(username=self.username)
        user.set_password(self.password)
        user.save()
        self.user = user

        # put together the login information
        mongodb_username = config("MONGODB_USERNAME")
        mongodb_password = config("MONGODB_PASSWORD")
        mongodb_database_url = config("MONGODB_DATABASE_URL")

        login_dict = {
            "mongodb_username": mongodb_username,
            "mongodb_password": mongodb_password,
            "mongodb_database_url": mongodb_database_url,
        }

        # create the storage entry in the models
        mongodb_entry = StorageProviderDb.objects.create(
            storage_type="mongodb",
            name="mongodbtest",
            owner=self.user,
            description="MongoDB storage provider for tests",
            login=login_dict,
            is_active=True,
        )
        mongodb_entry.full_clean()
        mongodb_entry.save()

    def tearDown(self) -> None:
        """
        Clean out the mongodb database.
        """
        # Remove all the collections that start with queued.
        mongodb_entry = StorageProviderDb.objects.get(name="mongodbtest")
        storage_provider = MongodbProvider(mongodb_entry.login, mongodb_entry.name)
        database = storage_provider.client["jobs"]
        for collection_name in database.list_collection_names():
            if collection_name.startswith("queued.dummy"):
                collection = database[collection_name]
                collection.drop()

        # Remove all the collections from results that start with dummy
        database = storage_provider.client["results"]
        for collection_name in database.list_collection_names():
            if collection_name.startswith("dummy"):
                collection = database[collection_name]
                collection.drop()

        # Remove all the collections from status that start with dummy
        database = storage_provider.client["status"]
        for collection_name in database.list_collection_names():
            if collection_name.startswith("dummy"):
                collection = database[collection_name]
                collection.drop()

    def test_mongodb_object(self):
        """
        Test that we can create a MongoDB object.
        """
        mongodb_entry = StorageProviderDb.objects.get(name="mongodbtest")
        mongodb_provider = MongodbProvider(mongodb_entry.login, mongodb_entry.name)
        self.assertIsNotNone(mongodb_provider)

        # test that we cannot create a dropbox object a poor login dict structure
        poor_login_dict = {
            "app_key_t": "test",
            "app_secret": "test",
            "refresh_token": "test",
        }
        with self.assertRaises(ValidationError):
            MongodbProvider(poor_login_dict, mongodb_entry.name)

    def test_not_active(self):
        """
        Test that we cannot work with the provider if it is not active.
        """
        entry = StorageProviderDb.objects.get(name="mongodbtest")
        entry.is_active = False
        storage_provider = MongodbProvider(entry.login, entry.name, entry.is_active)

        # make sure that we cannot upload if it is not active
        test_content = {"experiment_0": "Nothing happened here."}
        storage_path = "test/subcollection"

        job_id = uuid.uuid4().hex[:24]
        second_path = "test/subcollection_2"
        with self.assertRaises(ValueError):
            storage_provider.upload(test_content, storage_path, job_id)
        with self.assertRaises(ValueError):
            storage_provider.get_file_content(storage_path, job_id)
        with self.assertRaises(ValueError):
            storage_provider.move_file(storage_path, second_path, job_id)
        with self.assertRaises(ValueError):
            storage_provider.delete_file(second_path, job_id)

    def test_upload_etc(self):
        """
        Test that it is possible to upload a file.
        """

        # create a mongodb object
        mongodb_entry = StorageProviderDb.objects.get(name="mongodbtest")
        storage_provider = MongodbProvider(mongodb_entry.login, mongodb_entry.name)

        # upload a file and get it back
        test_content = {"experiment_0": "Nothing happened here."}
        storage_path = "test/subcollection"

        job_id = uuid.uuid4().hex[:24]
        storage_provider.upload(test_content, storage_path, job_id)
        test_result = storage_provider.get_file_content(storage_path, job_id)

        self.assertDictEqual(test_content, test_result)

        # move it and get it back
        second_path = "test/subcollection_2"
        storage_provider.move_file(storage_path, second_path, job_id)
        test_result = storage_provider.get_file_content(second_path, job_id)
        self.assertDictEqual(test_content, test_result)

        # clean up our mess
        storage_provider.delete_file(second_path, job_id)

    def test_configs(self):
        """
        Test that we are able to obtain a list of backends.
        """
        # create a mongodb object
        mongodb_entry = StorageProviderDb.objects.get(name="mongodbtest")
        storage_provider = MongodbProvider(mongodb_entry.login, mongodb_entry.name)

        # create a dummy config
        dummy_id = uuid.uuid4().hex[:5]
        dummy_dict: dict = {}
        dummy_dict["gates"] = []
        dummy_dict["name"] = "Dummy"
        dummy_dict["num_wires"] = 3
        dummy_dict["version"] = "0.0.1"
        dummy_dict["simulator"] = True
        backend_name = f"dummy{dummy_id}"
        dummy_dict["display_name"] = backend_name

        config_path = "backends/configs"
        mongo_id = uuid.uuid4().hex[:24]
        storage_provider.upload(dummy_dict, config_path, job_id=mongo_id)

        # can we get the backend in the list ?
        backends = storage_provider.get_backends()
        self.assertTrue(f"dummy{dummy_id}" in backends)

        # can we get the config of the backend ?
        backend_dict = storage_provider.get_backend_dict(backend_name)
        self.assertEqual(
            backend_dict["backend_name"],
            f"mongodbtest_{dummy_dict['display_name']}_simulator",
        )
        storage_provider.delete_file(config_path, mongo_id)

    def test_jobs(self):
        """
        Test that we can handle the necessary functions for the jobs and status.
        """
        # disable too many local variables
        # pylint: disable=R0914

        # create a mongodb object
        mongodb_entry = StorageProviderDb.objects.get(name="mongodbtest")
        storage_provider = MongodbProvider(mongodb_entry.login, mongodb_entry.name)

        # create a dummy config
        dummy_id = uuid.uuid4().hex[:5]
        dummy_dict: dict = {}
        dummy_dict["gates"] = []
        dummy_dict["name"] = "Dummy"
        dummy_dict["num_wires"] = 3
        dummy_dict["version"] = "0.0.1"

        backend_name = f"dummy{dummy_id}"
        dummy_dict["display_name"] = backend_name
        dummy_dict["simulator"] = True
        config_path = "backends/configs"
        mongo_id = uuid.uuid4().hex[:24]
        storage_provider.upload(dummy_dict, config_path, job_id=mongo_id)

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
        username = "dummy_user"

        job_id = storage_provider.upload_job(
            job_dict=job_payload, display_name=backend_name, username=username
        )
        self.assertTrue(len(job_id) > 1)

        # now also test that we can upload the status
        job_response_dict = storage_provider.upload_status(
            display_name=backend_name,
            username=username,
            job_id=job_id,
        )
        self.assertTrue(len(job_response_dict["job_id"]) > 1)
        # now test that we can get the job status
        job_status = storage_provider.get_status(
            display_name=backend_name,
            username=username,
            job_id=job_id,
        )
        self.assertFalse("_id" in job_status.keys())
        self.assertEqual(job_status["job_id"], job_id)

        # test that we can get a job result
        # first upload a dummy result
        dummy_result = {"results": "dummy"}
        result_json_dir = "results/" + backend_name
        storage_provider.upload(dummy_result, result_json_dir, job_id)

        # now get the result
        result = storage_provider.get_result(
            display_name=backend_name,
            username=username,
            job_id=job_id,
        )
        self.assertFalse("_id" in result.keys())
        self.assertEqual(dummy_result["results"], result["results"])

        # remove the obsolete job from the storage
        job_dir = "jobs/queued/" + backend_name
        storage_provider.delete_file(job_dir, job_id)

        # remove the obsolete collection from the storage
        database = storage_provider.client["jobs"]
        collection = database[f"queued.{backend_name}"]
        collection.drop()

        # remove the obsolete status from the storage
        status_dir = "status/" + backend_name
        storage_provider.delete_file(status_dir, job_id)

        # remove the obsolete collection from the storage
        database = storage_provider.client["status"]
        collection = database[backend_name]
        collection.drop()

        # remove the obsolete result from the storage
        storage_provider.delete_file(result_json_dir, job_id)
        # remove the obsolete collection from the storage
        database = storage_provider.client["results"]
        collection = database[backend_name]
        collection.drop()

        # remove the obsolete config from the storage
        storage_provider.delete_file(config_path, mongo_id)

    def test_backend_name(self):
        """
        Test that we separate out properly the backend names
        """
        short_test_name = "tests"
        short_name = get_short_backend_name(short_test_name)

        self.assertEqual(short_test_name, short_name)

        test_name = "alqor_tests_simulator"
        short_name = get_short_backend_name(test_name)
        self.assertEqual(short_test_name, short_name)

        test_name = "alqor_tests_simulator_crap"
        short_name = get_short_backend_name(test_name)
        self.assertEqual("", short_name)
