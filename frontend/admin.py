"""
Module that defines some basic properties of the app.
"""

from django.contrib import admin
from .models import Impressum

# Register your models here.
admin.site.register(Impressum)
