"""
The models that define our sql tables for the app.
"""

from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


class User(AbstractUser):
    """
    The class that will contain all the fancy features of a user.
    """


class Token(models.Model):
    """
    The backend class for the tokens that allow access to the different backends etc.

    Args:
        key: CharField, contains authorization token value.
        user: ForeignKey, foreign key to the logged user.
        created_at: DateTimeField, contains date and time of token creation.
        is_active: BooleanField contains if token is active.
    """

    key = models.CharField(max_length=40, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField()
    is_active = models.BooleanField(default=False)


class StorageProviderDb(models.Model):
    """
    This class allows users to access storage providers in the same way as they
    would access other systems. So it contains all the necessary information to access
    the storage provider and open a connection.

    Args:
        storage_type: The type of storage provider.
        name: The name of the storage provider. Has to be unique.
        owner: Which user owns this storage provider.
        description: An optional description of the storage provider.
        login: The login information for the storage provider.
    """

    STORAGE_TYPE_CHOICES = (
        ("dropbox", "Dropbox"),
        ("mongodb", "MongoDB"),
    )

    # the storage_type. It can be "dropbox" or "mongodb".
    storage_type = models.CharField(
        max_length=20,
        choices=STORAGE_TYPE_CHOICES,
    )

    # the name of the storage provider. Has to be unique.
    name = models.CharField(max_length=50, unique=True)

    # the owner of the storage provider.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    # an optional description of the storage provider.
    description = models.CharField(max_length=500, null=True)

    # the login information for the storage provider. This is a json string.
    login = models.JSONField()

    def clean(self):
        if self.storage_type not in dict(self.STORAGE_TYPE_CHOICES):
            raise ValidationError(
                {"storage_type": f"Value '{self.storage_type}' is not a valid choice."}
            )


class Backend(models.Model):
    """
    The backend class, which allows us to safe the properties of the backends etc.

    THIS CLASS IS OUTDATED and not used anymore.
    IT SHOULD BE SAFELY REMOVED AT SOME POINT.

    Args:
        name: The name of the backend under which we will identify it later
        description: A description of the backend as it will be given to the user
        version: The version of the backend
        cold_atom_type: describes what kind of backend you have. Fermions, spins or bosons ?
        gates: the allowed gates. They should be described through an appropiate json
        max_experiments: number of experiments the user is allowed to run.
        max_shots: How many shots of each experiment are allowed.
        simulator: Is the backend a simulator or real hardware ?
        supported_instructions: a json string with the support instructions.
        num_wires: The number of wires on which informaiton is stored. For compatibility with qiskit
            it is sent out as n_qubits in the config file.
        wire_order: Could by interleaved or sequential.
        num_species: Number of internal states the backend is working with. Only relevant for
            the types `boson` or `fermion`
    """

    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=500)
    version = models.CharField(max_length=20)
    COLD_ATOM_TYPE_CHOICES = (
        ("fermion", "fermion"),
        ("spin", "spin"),
        ("boson", "boson"),
    )
    cold_atom_type = models.CharField(max_length=15, choices=COLD_ATOM_TYPE_CHOICES)
    gates = models.JSONField(null=True)
    max_experiments = models.IntegerField(default=1000)
    max_shots = models.IntegerField(default=100000000)
    simulator = models.BooleanField(default=True)
    supported_instructions = models.JSONField(null=True)
    num_wires = models.PositiveIntegerField(default=1)
    WIRE_ORDER_CHOICES = (("interleaved", "interleaved"), ("sequential", "sequential"))
    wire_order = models.CharField(max_length=15, choices=WIRE_ORDER_CHOICES)
    num_species = models.PositiveIntegerField(default=1)
