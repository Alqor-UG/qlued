"""
Module that contains all the tests for this app folder.
"""

# pylint: disable=C0103
import json

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from backends.models import StorageProviderDb


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
        print(dropbox_entry.login["app_key"])

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

        poor_name = "test test"
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

        poor_name = "test_test"
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
