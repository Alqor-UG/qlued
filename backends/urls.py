"""
The url patterns that allow us to connect jobs that are defined in views to the
html addresses.
"""

from django.urls import path

from .api_v2 import api as api_v2

urlpatterns = [
    path("v2/", api_v2.urls),
]
