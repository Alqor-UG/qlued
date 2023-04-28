"""
The url patterns that allow us to connect jobs that are defined in views to the
html addresses.
"""

from django.urls import path
from backends import views

from .api_v1 import api as api_v1
from .api_v2 import api as api_v2

urlpatterns = [
    path("<str:backend_name>/get_config/", views.get_config_v2, name="get_config"),
    path("<str:backend_name>/post_job/", views.post_job, name="post_job"),
    path(
        "<str:backend_name>/get_job_status/",
        views.get_job_status,
        name="get_job_status",
    ),
    path(
        "<str:backend_name>/get_job_result/",
        views.get_job_result,
        name="get_job_result",
    ),
    path(
        "<str:backend_name>/get_user_jobs/", views.get_user_jobs, name="get_user_jobs"
    ),
    path("v1/", api_v1.urls),
    path("v2/", api_v2.urls),
]
