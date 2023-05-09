"""
The models that define our tests for this app.
"""
import json

from decouple import config
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .apps import BackendsConfig as ac

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

    def test_get_unknown_backend(self):
        """
        Test if we can nicely recover known backends and refuse unknown backends.
        """
        url = reverse("get_config", kwargs={"backend_name": "something_weird"})
        req = self.client.get(
            url, {"username": self.username, "password": self.password}
        )
        self.assertEqual(req.status_code, 404)

    def test_fermions_get_config(self):
        """
        Test the API that presents the capabilities of the backend
        """
        url = reverse("get_config", kwargs={"backend_name": "fermions"})
        req = self.client.get(
            url, {"username": self.username, "password": self.password}
        )
        data = json.loads(req.content)
        self.assertEqual(req.status_code, 200)
        self.assertCountEqual(data["basis_gates"], ["fhop", "fint", "fphase"])
        self.assertEqual(data["backend_name"], "alqor_fermionic_tweezer_simulator")
        self.assertEqual(data["display_name"], "fermions")

        base_url = config("BASE_URL")
        self.assertEqual(data["url"], base_url + "/api/fermions/")
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

    def test_singlequdit_get_config(self):
        """
        Test the API that presents the capabilities of the backend
        """
        url = reverse("get_config", kwargs={"backend_name": "singlequdit"})
        req = self.client.get(
            url, {"username": self.username, "password": self.password}
        )
        data = json.loads(req.content)
        self.assertEqual(data["display_name"], "singlequdit")
        self.assertEqual(data["backend_name"], "alqor_singlequdit_simulator")
        base_url = config("BASE_URL")
        self.assertEqual(data["url"], base_url + "/api/singlequdit/")
        self.assertEqual(data["backend_version"], "0.0.2")
        self.assertEqual(data["conditional"], False)
        self.assertEqual(data["local"], False)
        self.assertEqual(data["open_pulse"], False)
        self.assertEqual(data["memory"], True)
        self.assertEqual(data["coupling_map"], "linear")

        self.assertEqual(req.status_code, 200)

    def test_multiqudit_get_config(self):
        """
        Test the API that presents the capabilities of the backend
        """
        url = reverse("get_config", kwargs={"backend_name": "multiqudit"})
        req = self.client.get(
            url, {"username": self.username, "password": self.password}
        )
        data = json.loads(req.content)

        self.assertCountEqual(
            data["basis_gates"], ["rlx", "rlz", "rlz2", "rlxly", "rlzlz"]
        )
        self.assertEqual(data["backend_name"], "alqor_multiqudit_simulator")
        self.assertEqual(data["display_name"], "multiqudit")
        base_url = config("BASE_URL")
        self.assertEqual(data["url"], base_url + "/api/multiqudit/")
        self.assertEqual(data["max_experiments"], 1000)
        self.assertEqual(req.status_code, 200)
        gates = data["gates"]

        for gate in gates:
            if gate["name"] == "rlx":
                self.assertEqual(gate["coupling_map"], [[0], [1], [2], [3], [4]])
            if gate["name"] == "rlz":
                self.assertEqual(gate["coupling_map"], [[0], [1], [2], [3], [4]])
            if gate["name"] == "rlxly":
                self.assertEqual(
                    gate["coupling_map"],
                    [[0, 1], [1, 2], [2, 3], [3, 4], [0, 1, 2, 3, 4]],
                )


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
        self.storage_provider = getattr(ac, "storage")

    def test_post_job(self):
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

        url = reverse("post_job", kwargs={"backend_name": "fermions"})
        req = self.client.post(
            url,
            {
                "json": json.dumps(job_payload),
                "username": self.username,
                "password": self.password,
            },
        )
        data = json.loads(req.content)
        self.assertEqual(data["status"], "INITIALIZING")
        self.assertEqual(req.status_code, 200)

        if self.storage_provider.__class__.__name__ == "DropboxProvider":
            # clean up the file
            file_path = "Backend_files/Queued_Jobs/fermions"
            file_id = f"job-{data['job_id']}"
            self.storage_provider.delete_file(file_path, file_id)
            file_path = f"Backend_files/Status/fermions/{self.username}"
            file_id = f"status-{data['job_id']}"
            self.storage_provider.delete_file(file_path, file_id)
        elif self.storage_provider.__class__.__name__ == "MongodbProvider":
            print("MongodbProvider")
            storage_path = "jobs/queued/fermions"
            self.storage_provider.delete_file(storage_path, data["job_id"])

            storage_path = "status/fermions"
            self.storage_provider.delete_file(storage_path, data["job_id"])

    def test_get_job_status(self):
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

        url = reverse("post_job", kwargs={"backend_name": "fermions"})
        req = self.client.post(
            url,
            {
                "json": json.dumps(job_payload),
                "username": self.username,
                "password": self.password,
            },
        )
        data = json.loads(req.content)
        self.assertEqual(data["status"], "INITIALIZING")
        self.assertEqual(req.status_code, 200)

        req_id = data["job_id"]
        status_payload = {"job_id": req_id}
        url = reverse("get_job_status", kwargs={"backend_name": "fermions"})
        req = self.client.get(
            url,
            {
                "json": json.dumps(status_payload),
                "username": self.username,
                "password": self.password,
            },
        )
        self.assertEqual(req.status_code, 200)
        data = json.loads(req.content)
        self.assertEqual(data["job_id"], req_id)

    def test_get_job_result(self):
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

        url = reverse("post_job", kwargs={"backend_name": "fermions"})
        req = self.client.post(
            url,
            {
                "json": json.dumps(job_payload),
                "username": self.username,
                "password": self.password,
            },
        )
        data = json.loads(req.content)
        self.assertEqual(data["status"], "INITIALIZING")
        self.assertEqual(req.status_code, 200)

        req_id = data["job_id"]
        status_payload = {"job_id": req_id}
        url = reverse("get_job_result", kwargs={"backend_name": "fermions"})
        req = self.client.get(
            url,
            {
                "json": json.dumps(status_payload),
                "username": self.username,
                "password": self.password,
            },
        )
        self.assertEqual(req.status_code, 200)
        data = json.loads(req.content)
        self.assertEqual(data["job_id"], req_id)
