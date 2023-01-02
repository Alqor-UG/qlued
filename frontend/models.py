"""
The models that define our sql tables for the app.
"""

from django.db import models


class Impressum(models.Model):
    """
    A class for the impressum such that it is official who is behind this specific instance.
    Please be aware that there should be only one such value in the long term.
    """

    impressum = models.TextField(default="No impressum known.")
