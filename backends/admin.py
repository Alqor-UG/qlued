"""
Module that defines some basic properties of the app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Backend, StorageProviderDb

# Register your models here.

admin.site.register(User, UserAdmin)
admin.site.register(Backend)
admin.site.register(StorageProviderDb)
