"""
The tests for the local storage provider
"""
import uuid
import shutil

from decouple import config
from pydantic import ValidationError

from django.contrib.auth import get_user_model
from django.test import TestCase

from sqooler.storage_providers import LocalProviderExtended as LocalProvider
from sqooler.schemes import LocalLoginInformation, BackendConfigSchemaIn

from ..storage_providers import (
    get_short_backend_name,
    get_storage_provider_from_entry,
)

from ..models import StorageProviderDb

User = get_user_model()


class LocalProviderTest(TestCase):
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
        base_path = "storage"

        login_dict = {
            "base_path": base_path,
        }

        # create the storage entry in the models
        local_entry = StorageProviderDb.objects.create(
            storage_type="local",
            name="localtest",
            owner=self.user,
            description="Local storage provider for tests",
            login=login_dict,
            is_active=True,
        )
        local_entry.full_clean()
        local_entry.save()

    def tearDown(self):
        shutil.rmtree("storage", ignore_errors=True)

    def test_localdb_object(self):
        """
        Test that we can create a MongoDB object.
        """
        mongodb_entry = StorageProviderDb.objects.get(name="localtest")
        login_info = LocalLoginInformation(**mongodb_entry.login)
        mongodb_provider = LocalProvider(login_info, mongodb_entry.name)
        self.assertIsNotNone(mongodb_provider)

        # test that we cannot create a dropbox object a poor login dict structure
        poor_login_dict = {
            "app_key_t": "test",
            "app_secret": "test",
            "refresh_token": "test",
        }
        with self.assertRaises(ValidationError):
            login_info = LocalLoginInformation(**poor_login_dict)
            LocalProvider(login_info, mongodb_entry.name)

    def test_not_active(self):
        """
        Test that we cannot work with the provider if it is not active.
        """
        entry = StorageProviderDb.objects.get(name="localtest")
        entry.is_active = False
        login_info = LocalLoginInformation(**entry.login)
        storage_provider = LocalProvider(login_info, entry.name, entry.is_active)

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
        mongodb_entry = StorageProviderDb.objects.get(name="localtest")
        login_info = LocalLoginInformation(**mongodb_entry.login)
        storage_provider = LocalProvider(login_info, mongodb_entry.name)

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


class BackendsWithMultipleLocalProvidersTest(TestCase):
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

        # add the first storage provider
        base_path = "storage-3"

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
            "name": "alqor_fermionic-tweezer_simulator",
            "supported_instructions": [],
            "wire_order": "interleaved",
            "gates": [],
            "simulator": True,
            "num_wires": 2,
            "num_species": 1,
            "version": "0.0.1",
            "max_shots": 100,
            "max_experiments": 100,
            "cold_atom_type": "fermions",
            "description": "First device for tests",
            "operational": True,
        }

        local_storage = get_storage_provider_from_entry(local_entry)
        config_info = BackendConfigSchemaIn(**fermions_config)
        local_storage.upload_config(config_info, local_entry)

        # add the second storage provider
        base_path = "storage-4"

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
            "gates": [],
            "supported_instructions": [],
            "simulator": True,
            "num_wires": 1,
            "wire_order": "interleaved",
            "num_species": 1,
            "version": "0.0.1",
            "max_shots": 100,
            "max_experiments": 100,
            "cold_atom_type": "fermions",
            "description": "Second device for tests",
            "operational": True,
        }

        local_storage = get_storage_provider_from_entry(local_entry)
        config_info = BackendConfigSchemaIn(**single_qudit_config)
        local_storage.upload_config(config_info, local_entry)

    def tearDown(self):
        shutil.rmtree("storage-3")
        shutil.rmtree("storage-4")

    def test_get_backend_config(self):
        """
        Test that we get the appropiate config dictionnary
        """

        # first get the entry
        db_entry = StorageProviderDb.objects.get(name="local2")

        login_info = LocalLoginInformation(**db_entry.login)
        storage_provider = LocalProvider(login_info, db_entry.name)

        # now get the backend config
        config_info = storage_provider.get_backend_dict(display_name="singlequdit")
        assert config_info.backend_name == "local2_singlequdit_simulator"

        # now also test that the name overwrites the display name
        db_entry = StorageProviderDb.objects.get(name="local1")
        login_info = LocalLoginInformation(**db_entry.login)
        storage_provider = LocalProvider(login_info, db_entry.name)

        # now get the backend config
        config_info = storage_provider.get_backend_dict(display_name="fermions")
        assert config_info.backend_name == "local1_fermions_simulator"
