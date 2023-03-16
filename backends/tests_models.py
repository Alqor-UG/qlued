"""
Test the models of this app.
"""
import json

from decouple import config
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Backend
from .apps import BackendsConfig as ac

User = get_user_model()

# pylint: disable=E1101
class BackendCreationTest(TestCase):
    """
    The test for the creation of the backends.
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