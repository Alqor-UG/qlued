"""
The models that define our tests for the api in version 1.
"""
import json
from datetime import datetime
import uuid
import shutil

import pytz


from decouple import config
from django.test import TestCase
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model

from sqooler.storage_providers import MongodbProviderExtended as MongodbProvider
from sqooler.schemes import MongodbLoginInformation
from ..models import Token, StorageProviderDb
from ..storage_providers import get_storage_provider_from_entry

User = get_user_model()


class BackendConfigTest(TestCase):
    """
    The class that contains all the tests for this backends app.
    """

    fixtures = ["backend.json"]

    def setUp(self):
        self.username = config("USERNAME_TEST")
        self.password = config("PASSWORD_TEST")
        user = User.objects.create(username=self.username)
        user.set_password(self.password)
        user.save()

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
            name="alqor",
            owner=user,
            description="MongoDB storage provider for tests",
            login=login_dict,
        )
        mongodb_entry.full_clean()
        mongodb_entry.save()

    def test_fermions_get_config_ninja(self):
        """
        Test the API that presents the capabilities of the backend through the new version
         of the API
        """
        url = reverse_lazy("api-2.0.0:get_config", kwargs={"backend_name": "fermions"})
        req = self.client.get(url)
        data = json.loads(req.content)
        self.assertEqual(req.status_code, 200)
        self.assertCountEqual(data["basis_gates"], ["fhop", "fint", "fphase"])
        self.assertEqual(data["backend_name"], "alqor_fermions_simulator")
        self.assertEqual(data["display_name"], "fermions")

        base_url = config("BASE_URL")
        self.assertEqual(data["url"], base_url + "/api/v2/alqor_fermions_simulator/")
        self.assertEqual(data["n_qubits"], 8)
        self.assertEqual(data["num_species"], 2)
        gates = data["gates"]
        for gate in gates:
            if gate["name"] == "fhop":
                self.assertEqual(
                    gate["coupling_map"],
                    [
                        [0, 1, 2, 3],
                        [2, 3, 4, 5],
                        [4, 5, 6, 7],
                        [0, 1, 2, 3, 4, 5, 6, 7],
                    ],
                )
            if gate["name"] == "fint":
                self.assertEqual(gate["coupling_map"], [[0, 1, 2, 3, 4, 5, 6, 7]])

        # test also with its full name

        url = reverse_lazy(
            "api-2.0.0:get_config",
            kwargs={"backend_name": "alqor_singlequdit_simulator"},
        )
        req = self.client.get(url)
        data = json.loads(req.content)
        self.assertEqual(req.status_code, 200)
        self.assertEqual(data["backend_name"], "alqor_singlequdit_simulator")
        self.assertEqual(data["display_name"], "singlequdit")

    def test_get_backend_status(self):
        """
        Test the API that presents the status of the backend
        """
        url = reverse_lazy(
            "api-2.0.0:get_backend_status",
            kwargs={"backend_name": "alqor_fermions_simulator"},
        )
        req = self.client.get(url)
        data = json.loads(req.content)
        self.assertEqual(req.status_code, 200)

        # get the name
        self.assertEqual(data["backend_name"], "alqor_fermions_simulator")

        # get the version
        self.assertEqual(data["backend_version"], "0.1")

        # get the operational status
        self.assertEqual(data["operational"], True)

        # get the pending jobs
        self.assertEqual(data["pending_jobs"], 0)

        # get the status message
        self.assertEqual(data["status_msg"], "")

    def test_get_backends_ninja(self):
        """
        Test that we are able to obtain the config of all the backends.
        """
        url = reverse_lazy("api-2.0.0:get_backends")
        req = self.client.get(url)
        data = json.loads(req.content)
        self.assertEqual(req.status_code, 200)
        self.assertTrue(len(data) >= 4)


class JobSubmissionTest(TestCase):
    """
    The class that contains all the tests for this backends app.
    """

    fixtures = ["backend.json"]

    def setUp(self):
        # create a user
        self.username = config("USERNAME_TEST")
        self.password = config("PASSWORD_TEST")
        user = User.objects.create(username=self.username)
        user.set_password(self.password)
        user.save()

        # give the user a token
        key = uuid.uuid4().hex
        self.token = Token.objects.create(
            key=key, user=user, created_at=datetime.now(pytz.utc), is_active=True
        )

        # get the storage
        login_dict = {
            "mongodb_username": config("MONGODB_USERNAME"),
            "mongodb_password": config("MONGODB_PASSWORD"),
            "mongodb_database_url": config("MONGODB_DATABASE_URL"),
        }

        # create the storage entry in the models
        mongodb_entry = StorageProviderDb.objects.create(
            storage_type="mongodb",
            name="alqor",
            owner=user,
            description="MongoDB storage provider for tests",
            login=login_dict,
        )
        mongodb_entry.full_clean()
        mongodb_entry.save()

    def test_post_job_ninja(self):
        """
        Test the API that presents the capabilities of the backend
        """
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

        url = reverse_lazy("api-2.0.0:post_job", kwargs={"backend_name": "fermions"})

        req = self.client.post(
            url,
            {"job": json.dumps(job_payload), "token": self.token.key},
            content_type="application/json",
        )
        data = json.loads(req.content)
        self.assertEqual(data["status"], "INITIALIZING")
        self.assertEqual(req.status_code, 200)

        # test that we cannot create a job with invalid token
        req = self.client.post(
            url,
            {"job": json.dumps(job_payload), "token": "DUMMY"},
            content_type="application/json",
        )
        data = req.json()
        self.assertEqual(data["status"], "ERROR")

    def test_get_job_status_ninja(self):
        """
        Test the API that checks the job status
        """
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
        url = reverse_lazy("api-2.0.0:post_job", kwargs={"backend_name": "fermions"})

        req = self.client.post(
            url,
            {"job": json.dumps(job_payload), "token": self.token.key},
            content_type="application/json",
        )

        data = json.loads(req.content)
        self.assertEqual(data["status"], "INITIALIZING")
        self.assertEqual(req.status_code, 200)

        req_id = data["job_id"]
        url = reverse_lazy(
            "api-2.0.0:get_job_status", kwargs={"backend_name": "fermions"}
        )

        req = self.client.get(
            url,
            {"job_id": req_id, "token": self.token.key},
        )
        self.assertEqual(req.status_code, 200)
        data = json.loads(req.content)
        self.assertEqual(data["job_id"], req_id)

        # create a mongodb object
        mongodb_entry = StorageProviderDb.objects.get(name="alqor")
        login_info = MongodbLoginInformation(**mongodb_entry.login)
        storage_provider = MongodbProvider(login_info, mongodb_entry.name)

        # verify if the storageprovider is of the type DropboxProvider or MongodbProvider
        if storage_provider.__class__.__name__ == "DropboxProvider":
            # clean up the file
            storage_path = "Backend_files/Queued_Jobs/fermions"
            job_id = f"job-{data['job_id']}"
            storage_provider.delete_file(storage_path, job_id)

            storage_path = f"/Backend_files/Status/fermions/{self.username}"
            job_id = f"status-{data['job_id']}"
            storage_provider.delete_file(storage_path, job_id)
        elif storage_provider.__class__.__name__ == "MongodbProvider":
            storage_path = "jobs/queued/fermions"
            storage_provider.delete_file(storage_path, data["job_id"])

            storage_path = "status/fermions"
            storage_provider.delete_file(storage_path, data["job_id"])

    def test_get_job_result_ninja(self):
        """
        Test the API that checks the job status
        """
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
        url = reverse_lazy("api-2.0.0:post_job", kwargs={"backend_name": "fermions"})

        req = self.client.post(
            url,
            {"job": json.dumps(job_payload), "token": self.token.key},
            content_type="application/json",
        )

        data = json.loads(req.content)
        self.assertEqual(data["status"], "INITIALIZING")
        self.assertEqual(req.status_code, 200)

        req_id = data["job_id"]
        url = reverse_lazy(
            "api-2.0.0:get_job_result", kwargs={"backend_name": "fermions"}
        )

        req = self.client.get(
            url,
            {"job_id": req_id, "token": self.token.key},
        )
        self.assertEqual(req.status_code, 200)
        data = json.loads(req.content)
        self.assertEqual(data["job_id"], req_id)


class JobSubmissionWithMultipleLocalProvidersTest(TestCase):
    """
    The class that contains tests for multiple providers. Based on
    a local storage, so without a connection to the spooler.
    """

    def setUp(self):
        # create a user
        self.username = config("USERNAME_TEST")
        self.password = config("PASSWORD_TEST")
        user = User.objects.create(username=self.username)
        user.set_password(self.password)
        user.save()

        # give the user a token
        key = uuid.uuid4().hex
        self.token = Token.objects.create(
            key=key, user=user, created_at=datetime.now(pytz.utc), is_active=True
        )

        # add the first storage provider
        base_path = "storage-1"

        login_dict = {
            "base_path": base_path,
        }

        local_entry = StorageProviderDb.objects.create(
            storage_type="local",
            name="local1",
            owner=user,
            description="First storage provider for tests",
            login=login_dict,
        )
        local_entry.full_clean()
        local_entry.save()

        # create a dummy config for the required fermions
        fermions_config = {
            "display_name": "fermions",
        }

        local_storage = get_storage_provider_from_entry(local_entry)
        local_storage.upload(fermions_config, "backends/configs", "fermions")

        # add the second storage provider
        base_path = "storage-2"

        login_dict = {
            "base_path": base_path,
        }

        local_entry = StorageProviderDb.objects.create(
            storage_type="local",
            name="local2",
            owner=user,
            description="Second storage provider for tests",
            login=login_dict,
        )
        local_entry.full_clean()
        local_entry.save()

        # create a dummy config for the required single qudit
        single_qudit_config = {
            "display_name": "singlequdit",
        }

        local_storage = get_storage_provider_from_entry(local_entry)
        local_storage.upload(single_qudit_config, "backends/configs", "singlequdit")

    def tearDown(self):
        shutil.rmtree("storage-1")
        shutil.rmtree("storage-2")

    def test_post_job_ninja(self):
        """
        Test the API that presents the capabilities of the backend
        """
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

        url = reverse_lazy(
            "api-2.0.0:post_job", kwargs={"backend_name": "local1_fermions_simulator"}
        )

        req = self.client.post(
            url,
            {"job": json.dumps(job_payload), "token": self.token.key},
            content_type="application/json",
        )
        data = json.loads(req.content)
        self.assertEqual(data["status"], "INITIALIZING")
        self.assertEqual(req.status_code, 200)

        # test that we cannot create a job with the wrong provider
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

        url = reverse_lazy(
            "api-2.0.0:post_job", kwargs={"backend_name": "local2_fermions_simulator"}
        )

        req = self.client.post(
            url,
            {"job": json.dumps(job_payload), "token": self.token.key},
            content_type="application/json",
        )
        data = json.loads(req.content)
        self.assertEqual(data["status"], "ERROR")
        self.assertEqual(req.status_code, 404)

        # test that we cannot create a job with invalid token
        req = self.client.post(
            url,
            {"job": json.dumps(job_payload), "token": "DUMMY"},
            content_type="application/json",
        )
        data = req.json()
        self.assertEqual(data["status"], "ERROR")

    def test_get_job_status_ninja(self):
        """
        Test the API that checks the job status
        """
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
        url = reverse_lazy(
            "api-2.0.0:post_job", kwargs={"backend_name": "local1_fermions_simulator"}
        )

        req = self.client.post(
            url,
            {"job": json.dumps(job_payload), "token": self.token.key},
            content_type="application/json",
        )

        data = json.loads(req.content)
        self.assertEqual(data["status"], "INITIALIZING")
        self.assertEqual(req.status_code, 200)

        req_id = data["job_id"]
        url = reverse_lazy(
            "api-2.0.0:get_job_status",
            kwargs={"backend_name": "local1_fermions_simulator"},
        )

        req = self.client.get(
            url,
            {"job_id": req_id, "token": self.token.key},
        )
        self.assertEqual(req.status_code, 200)
        data = json.loads(req.content)
        self.assertEqual(data["job_id"], req_id)

    def test_get_job_result_ninja(self):
        """
        Test the API that checks the job status
        """
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
        url = reverse_lazy(
            "api-2.0.0:post_job", kwargs={"backend_name": "local1_fermions_simulator"}
        )

        req = self.client.post(
            url,
            {"job": json.dumps(job_payload), "token": self.token.key},
            content_type="application/json",
        )

        data = json.loads(req.content)
        self.assertEqual(data["status"], "INITIALIZING")
        self.assertEqual(req.status_code, 200)

        req_id = data["job_id"]
        url = reverse_lazy(
            "api-2.0.0:get_job_result",
            kwargs={"backend_name": "local1_fermions_simulator"},
        )

        req = self.client.get(
            url,
            {"job_id": req_id, "token": self.token.key},
        )
        self.assertEqual(req.status_code, 200)
        data = json.loads(req.content)
        self.assertEqual(data["job_id"], req_id)
