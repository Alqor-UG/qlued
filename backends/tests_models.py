"""
Test the models of this app.
"""
from datetime import datetime
import uuid

import pytz

from decouple import config
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError

from .models import Backend, Token, StorageProviderDb

User = get_user_model()


class TokenCreationTest(TestCase):
    """
    The test for token creation etc.
    """

    def setUp(self):
        self.username = config("USERNAME_TEST")
        self.password = config("PASSWORD_TEST")
        user = User.objects.create(username=self.username)
        user.set_password(self.password)
        user.save()
        self.user = user

    def test_token_creation(self):
        """
        Test that we can properly create tokens.
        """

        key = uuid.uuid4().hex
        token = Token.objects.create(
            key=key, user=self.user, created_at=datetime.now(pytz.utc), is_active=True
        )
        self.assertEqual(token.key, key)

        # make sure that we cannot create a second token with the same key
        with self.assertRaises(IntegrityError):
            _ = Token.objects.create(
                key=key,
                user=self.user,
                created_at=datetime.now(pytz.utc),
                is_active=True,
            )


# pylint: disable=E1101
class BackendCreationTest(TestCase):
    """
    The test for the creation of the backends.

    THIS SHOULD BE REMOVED AT SOME POINT AS THIS CLASS IS NOW DEPRECEATED.
    """

    def test_fermion_creation(self):
        """
        Can we create the standard fermion backend ?
        """

        payload = {
            "name": "fermions",
            "description": "simulator of a fermionic tweezer hardware. "
            "The even wires denote the occupations of the spin-up fermions and "
            "the odd wires denote the spin-down fermions",
            "version": "0.0.1",
            "cold_atom_type": "fermion",
            "gates": [
                {
                    "coupling_map": [
                        [0, 1, 2, 3],
                        [2, 3, 4, 5],
                        [4, 5, 6, 7],
                        [0, 1, 2, 3, 4, 5, 6, 7],
                    ],
                    "description": "hopping of atoms to neighboring tweezers",
                    "name": "fhop",
                    "parameters": ["j_i"],
                    "qasm_def": "{}",
                },
                {
                    "coupling_map": [[0, 1, 2, 3, 4, 5, 6, 7]],
                    "description": "on-site interaction of atoms of opposite spin "
                    "state",
                    "name": "fint",
                    "parameters": ["u"],
                    "qasm_def": "{}",
                },
                {
                    "coupling_map": [
                        [0, 1],
                        [2, 3],
                        [4, 5],
                        [6, 7],
                        [0, 1, 2, 3, 4, 5, 6, 7],
                    ],
                    "description": "Applying a local phase to tweezers through an "
                    "external potential",
                    "name": "fphase",
                    "parameters": ["mu_i"],
                    "qasm_def": "{}",
                },
            ],
            "max_experiments": 1000,
            "max_shots": 1000000,
            "simulator": True,
            "supported_instructions": [
                "load",
                "measure",
                "barrier",
                "fhop",
                "fint",
                "fphase",
            ],
            "wire_order": "interleaved",
        }

        fermion_backend = Backend.objects.create(**payload)
        self.assertEqual(fermion_backend.wire_order, "interleaved")
        self.assertTrue(fermion_backend.simulator, True)

    def test_singlequdit_creation(self):
        """
        Can we create the standard fermion backend ?
        """

        payload = {
            "name": "singlequdit",
            "description": "Setup of a cold atomic gas experiment with a single qudit.",
            "version": "0.0.2",
            "cold_atom_type": "spin",
            "gates": [
                {
                    "name": "rlz",
                    "parameters": ["delta"],
                    "qasm_def": "gate rlz(delta) {}",
                    "coupling_map": [[0], [1], [2], [3], [4]],
                    "description": "Evolution under the Z gate",
                },
                {
                    "name": "rlz2",
                    "parameters": ["chi"],
                    "qasm_def": "gate rlz2(chi) {}",
                    "coupling_map": [[0], [1], [2], [3], [4]],
                    "description": "Evolution under lz2",
                },
                {
                    "name": "rlx",
                    "parameters": ["omega"],
                    "qasm_def": "gate lrx(omega) {}",
                    "coupling_map": [[0], [1], [2], [3], [4]],
                    "description": "Evolution under Lx",
                },
            ],
            "max_experiments": 1000,
            "max_shots": 1000000,
            "simulator": True,
            "supported_instructions": [
                "rlx",
                "rlz",
                "rlz2",
                "measure",
                "barrier",
                "load",
            ],
            "num_wires": 1,
            "wire_order": "interleaved",
        }

        singlequdit_backend = Backend.objects.create(**payload)
        self.assertTrue(singlequdit_backend.simulator, True)
        self.assertEqual(singlequdit_backend.num_wires, 1)

    def test_multiqudit_creation(self):
        """
        Can we create the standard fermion backend ?
        """

        payload = {
            "name": "multiqudit",
            "description": "Setup of a cold atomic gas experiment with a multiple qudits.",
            "version": "0.0.1",
            "cold_atom_type": "spin",
            "gates": [
                {
                    "name": "rlz",
                    "parameters": ["delta"],
                    "qasm_def": "gate rlz(delta) {}",
                    "coupling_map": [[0], [1], [2], [3], [4]],
                    "description": "Evolution under the Z gate",
                },
                {
                    "name": "rlz2",
                    "parameters": ["chi"],
                    "qasm_def": "gate rlz2(chi) {}",
                    "coupling_map": [[0], [1], [2], [3], [4]],
                    "description": "Evolution under Lz2",
                },
                {
                    "name": "rlx",
                    "parameters": ["omega"],
                    "qasm_def": "gate lrx(omega) {}",
                    "coupling_map": [[0], [1], [2], [3], [4]],
                    "description": "Evolution under Lx",
                },
                {
                    "name": "rlxly",
                    "parameters": ["J"],
                    "qasm_def": "gate rlylx(J) {}",
                    "coupling_map": [[0, 1], [1, 2], [2, 3], [3, 4], [0, 1, 2, 3, 4]],
                    "description": "Entanglement between neighboring gates with an xy interaction",
                },
            ],
            "max_experiments": 1000,
            "max_shots": 1000000,
            "simulator": True,
            "supported_instructions": [
                "rlx",
                "rlz",
                "rlz2",
                "rlxly",
                "barrier",
                "measure",
                "load",
            ],
            "num_wires": 4,
            "wire_order": "interleaved",
        }

        multiqudit_backend = Backend.objects.create(**payload)
        self.assertTrue(multiqudit_backend.simulator, True)
        self.assertEqual(multiqudit_backend.num_wires, 4)
        self.assertEqual(multiqudit_backend.max_experiments, 1000)


class StorageProviderDbCreationTest(TestCase):
    """
    Test if it is possible to create a dropbox storage
    """

    def setUp(self):
        self.username = config("USERNAME_TEST")
        self.password = config("PASSWORD_TEST")
        user = User.objects.create(username=self.username)
        user.set_password(self.password)
        user.save()
        self.user = user

    def test_mongo_storage_db_creation(self):
        """
        Test that we can properly create a storage provide with mongodb.
        """
        mongodb_username = config("MONGODB_USERNAME")
        mongodb_password = config("MONGODB_PASSWORD")
        mongodb_database_url = config("MONGODB_DATABASE_URL")
        login_dict = {
            "username": mongodb_username,
            "password": mongodb_password,
            "database_url": mongodb_database_url,
        }

        # create the storage entry in the models
        mongo_entry = StorageProviderDb.objects.create(
            storage_type="mongodb",
            name="mongodb_test",
            owner=self.user,
            description="MongoDB storage provider for tests",
            login=login_dict,
        )
        mongo_entry.full_clean()
        self.assertEqual(mongo_entry.owner, self.user)

        # make sure that we cannot some random storage type
        mongo_stupid = StorageProviderDb.objects.create(
            storage_type="mongodb_random",
            name="mongodb_test_2",
            owner=self.user,
            description="MongoDB storage provider for tests",
            login=login_dict,
        )
        with self.assertRaises(ValidationError):
            mongo_stupid.full_clean()

        # make sure that we cannot create a second storageprovide with the same name
        with self.assertRaises(IntegrityError):
            _ = StorageProviderDb.objects.create(
                storage_type="mongodb",
                name="mongodb_test",
                owner=self.user,
                description="MongoDB storage provider for tests",
                login=login_dict,
            )

    def test_drobox_creation(self):
        """
        Test that we can properly create a storage provide with Dropbox.
        """
        app_key = config("APP_KEY")
        app_secret = config("APP_SECRET")
        refresh_token = config("REFRESH_TOKEN")

        login_dict = {
            "app_key": app_key,
            "app_secret": app_secret,
            "refresh_token": refresh_token,
        }

        # create the storage entry in the models
        dropbox_entry = StorageProviderDb.objects.create(
            storage_type="dropbox",
            name="dropbox_test",
            owner=self.user,
            description="Dropbox storage provider for tests",
            login=login_dict,
        )
        dropbox_entry.full_clean()
        self.assertEqual(dropbox_entry.owner, self.user)

        # make sure that we cannot create a second storageprovide with the same name
        with self.assertRaises(IntegrityError):
            _ = StorageProviderDb.objects.create(
                storage_type="dropbox",
                name="dropbox_test",
                owner=self.user,
                description="Dropbox storage provider for tests",
                login=login_dict,
            )
