"""
Module that contains all the tests for this app folder.
"""

# pylint: disable=C0103
import json
import shutil

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from django.urls import reverse
from icecream import ic

from qlued.models import StorageProviderDb
from qlued.storage_providers import get_storage_provider_from_entry


class IndexPageTests(TestCase):
    """
    Test the title page
    """

    def test_call_index(self):
        """
        is it possible to reach the index page ?
        """
        url = reverse("index")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)


class JobSubmissionTest(TestCase):
    """
    Test basic properties of the job submission process.
    """

    def setUp(self):
        self.username = "sandy"
        self.password = "dog"
        user = get_user_model().objects.create(username=self.username)
        user.set_password(self.password)
        user.save()


class AddStorageProviderTest(TestCase):
    """
    Test the add storage provider page
    """

    def setUp(self):
        self.username = "sandy"
        self.password = "dog"
        user = get_user_model().objects.create(username=self.username)
        user.set_password(self.password)
        user.save()

    def test_call_add_storage_provider(self):
        """
        is it possible to reach the add storage provider page ?
        """

        url = reverse("add_storage_provider")
        r = self.client.get(url)
        # should fail because the user was not logged in
        self.assertEqual(r.status_code, 302)

        self.client.login(username=self.username, password=self.password)
        url = reverse("add_storage_provider")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

    def test_add_storage_provider(self):
        """
        is it possible to add a storage provider ?
        """

        self.client.login(username=self.username, password=self.password)
        url = reverse("add_storage_provider")

        login_dict = {
            "app_key": "app_key",
            "app_secret": "app_secret",
            "refresh_token": "refresh_token",
        }
        data = {
            "storage_type": "dropbox",
            "name": "test",
            "description": "test",
            "login": json.dumps(login_dict),
        }
        r = self.client.post(url, data)
        self.assertEqual(r.status_code, 302)

        # now it is also time to test that the storage provider was added properly
        dropbox_entry = StorageProviderDb.objects.get(name="test")
        self.assertEqual(dropbox_entry.storage_type, "dropbox")
        self.assertEqual(dropbox_entry.owner.username, self.username)

    def test_add_storage_provider_wrong_type(self):
        """
        is it possible to add a storage provider with a wrong type ?
        """

        self.client.login(username=self.username, password=self.password)
        url = reverse("add_storage_provider")
        login_dict = {
            "app_key": "app_key",
            "app_secret": "app_secret",
            "refresh_token": "refresh_token",
        }
        data = {
            "storage_type": "wrong",
            "name": "test",
            "description": "test",
            "login": json.dumps(login_dict),
        }
        r = self.client.post(url, data)
        self.assertEqual(r.status_code, 200)
        with self.assertRaises(ObjectDoesNotExist):
            StorageProviderDb.objects.get(name="test")

    def test_add_storage_provider_poor_name(self):
        """
        is it possible to add a storage provider with poor name ?
        """

        self.client.login(username=self.username, password=self.password)
        url = reverse("add_storage_provider")
        poor_names = ["test test", "test_test"]
        for poor_name in poor_names:
            login_dict = {
                "app_key": "app_key",
                "app_secret": "app_secret",
                "refresh_token": "refresh_token",
            }
            data = {
                "storage_type": "dropbox",
                "name": poor_name,
                "description": "test",
                "login": json.dumps(login_dict),
            }
            r = self.client.post(url, data)
            self.assertEqual(r.status_code, 200)
            with self.assertRaises(ObjectDoesNotExist):
                StorageProviderDb.objects.get(name=poor_name)

    def test_edit_storage_provider(self):
        """
        Test that we can nicely edit a storage provider
        """

        self.client.login(username=self.username, password=self.password)
        url = reverse("add_storage_provider")

        login_dict = {
            "app_key": "app_key",
            "app_secret": "app_secret",
            "refresh_token": "refresh_token",
        }
        data = {
            "storage_type": "dropbox",
            "name": "test",
            "description": "test",
            "login": json.dumps(login_dict),
            "is_active": True,
        }
        r = self.client.post(url, data)
        self.assertEqual(r.status_code, 302)

        # now it is also time to test that the storage provider was added properly
        dropbox_entry = StorageProviderDb.objects.get(name="test")
        data = {
            "storage_type": "dropbox",
            "name": "test",
            "description": "another test",
            "login": json.dumps(login_dict),
            "is_active": False,
        }
        url = reverse("edit_storage_provider", args=[dropbox_entry.pk])
        r = self.client.post(url, data)
        self.assertEqual(r.status_code, 302)
        dropbox_entry = StorageProviderDb.objects.get(name="test")
        self.assertEqual(dropbox_entry.description, "another test")
        self.assertEqual(dropbox_entry.is_active, False)

    def test_delete_storage_provider(self):
        """
        Can we also remove a storage provider ?
        """
        self.client.login(username=self.username, password=self.password)
        url = reverse("add_storage_provider")

        login_dict = {
            "app_key": "app_key",
            "app_secret": "app_secret",
            "refresh_token": "refresh_token",
        }
        data = {
            "storage_type": "dropbox",
            "name": "test",
            "description": "test",
            "login": json.dumps(login_dict),
        }
        r = self.client.post(url, data)
        self.assertEqual(r.status_code, 302)

        # now remove the storage provider
        dropbox_entry = StorageProviderDb.objects.get(name="test")
        url = reverse("delete_storage_provider", args=[dropbox_entry.pk])
        r = self.client.post(url, data)
        self.assertEqual(r.status_code, 302)
        with self.assertRaises(ObjectDoesNotExist):
            StorageProviderDb.objects.get(name="test")


class DevicesTest(TestCase):
    """
    Test the devices page
    """

    def setUp(self):
        self.username = "sandy"
        self.password = "dog"
        user = get_user_model().objects.create(username=self.username)
        user.set_password(self.password)
        user.save()

    def tearDown(self):
        shutil.rmtree("storage-1")

    def test_call_devices(self):
        """
        is it possible to add a storage provider ?
        """

        self.client.login(username=self.username, password=self.password)
        url = reverse("add_storage_provider")

        login_dict = {
            "base_path": "storage-1",
        }
        data = {
            "storage_type": "local",
            "name": "test",
            "description": "test",
            "login": json.dumps(login_dict),
        }
        r = self.client.post(url, data)
        self.assertEqual(r.status_code, 302)

        # now also try to see the devices page, even if no backend exists yet.
        url = reverse("devices")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

        # now with the backend config added
        local_entry = StorageProviderDb.objects.get(name="test")
        fermions_config = {
            "display_name": "fermions",
            "name": "fermions",
            "gates": [{"description": "Fermionic hopping gate", "name": "fhop"}],
            "supported_instructions": ["fhop"],
            "num_wires": 2,
            "version": "0.1",
            "simulator": True,
            "wire_order": "interleaved",
            "cold_atom_type": "fermion",
            "max_shots": 5,
            "max_experiments": 5,
            "description": "Dummy simulator for testing",
            "num_species": 1,
        }

        local_storage = get_storage_provider_from_entry(local_entry)
        local_storage.upload(fermions_config, "backends/configs", "fermions")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

        # now test that we have the appropriate information in each device
        devices = r.context["backend_list"]
        for device in devices:
            self.assertIsNotNone(
                device["url"], "Device dictionary does not contain valid url"
            )
            ic(device["operational"])

            # assert that the operational status is part of the device dictionary
            self.assertIn("operational", device)
