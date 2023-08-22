"""
The models that define our tests for the api in version 1.
"""
import json

from decouple import config
from django.test import TestCase
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model

from ..models import StorageProviderDb
from ..storage_providers import MongodbProvider

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

    def test_fermions_get_config_ninja(self):
        """
        Test the API that presents the capabilities of the backend through the new version
         of the API
        """
        url = reverse_lazy("api-1.0.0:get_config", kwargs={"backend_name": "fermions"})
        req = self.client.get(
            url, {"username": self.username, "password": self.password}
        )
        data = json.loads(req.content)
        self.assertEqual(req.status_code, 200)
        self.assertCountEqual(data["basis_gates"], ["fhop", "fint", "fphase"])
        self.assertEqual(data["backend_name"], "alqor_fermions_simulator")
        self.assertEqual(data["display_name"], "fermions")

        base_url = config("BASE_URL")
        self.assertEqual(data["url"], base_url + "/api/v1/fermions/")
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

    def test_get_backends_ninja(self):
        """
        Test that we are able to obtain the config of all the backends.
        """
        url = reverse_lazy("api-1.0.0:get_backends")
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
        self.username = config("USERNAME_TEST")
        self.password = config("PASSWORD_TEST")
        user = User.objects.create(username=self.username)
        user.set_password(self.password)
        user.save()

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

        url = reverse_lazy("api-1.0.0:post_job", kwargs={"backend_name": "fermions"})

        req = self.client.post(
            url,
            {
                "job": json.dumps(job_payload),
                "username": self.username,
                "password": self.password,
            },
            content_type="application/json",
        )
        data = json.loads(req.content)
        self.assertEqual(data["status"], "INITIALIZING")
        self.assertEqual(req.status_code, 200)

        mongodb_entry = StorageProviderDb.objects.get(name="alqor")
        storage_provider = MongodbProvider(mongodb_entry.login, mongodb_entry.name)

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
            print("MongodbProvider")
            storage_path = "jobs/queued/fermions"
            storage_provider.delete_file(storage_path, data["job_id"])

            storage_path = "status/fermions"
            storage_provider.delete_file(storage_path, data["job_id"])

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
        url = reverse_lazy("api-1.0.0:post_job", kwargs={"backend_name": "fermions"})

        req = self.client.post(
            url,
            {
                "job": json.dumps(job_payload),
                "username": self.username,
                "password": self.password,
            },
            content_type="application/json",
        )

        data = json.loads(req.content)
        self.assertEqual(data["status"], "INITIALIZING")
        self.assertEqual(req.status_code, 200)

        req_id = data["job_id"]
        url = reverse_lazy(
            "api-1.0.0:get_job_status", kwargs={"backend_name": "fermions"}
        )

        req = self.client.get(
            url,
            {
                "job_id": req_id,
                "username": self.username,
                "password": self.password,
            },
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
        url = reverse_lazy("api-1.0.0:post_job", kwargs={"backend_name": "fermions"})

        req = self.client.post(
            url,
            {
                "job": json.dumps(job_payload),
                "username": self.username,
                "password": self.password,
            },
            content_type="application/json",
        )

        data = json.loads(req.content)
        self.assertEqual(data["status"], "INITIALIZING")
        self.assertEqual(req.status_code, 200)

        req_id = data["job_id"]
        url = reverse_lazy(
            "api-1.0.0:get_job_result", kwargs={"backend_name": "fermions"}
        )

        req = self.client.get(
            url,
            {
                "job_id": req_id,
                "username": self.username,
                "password": self.password,
            },
        )
        self.assertEqual(req.status_code, 200)
        data = json.loads(req.content)
        self.assertEqual(data["job_id"], req_id)
