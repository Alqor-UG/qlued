"""main URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib.auth import views as auth_views
from django.contrib import admin
from django.urls import path, include
from frontend import views

urlpatterns = [
    path("", views.index, name="index"),
    path("about", views.about, name="about"),
    path("accounts/profile", views.profile, name="profile"),
    path("devices", views.devices, name="devices"),
    path(
        "add_storage_provider", views.add_storage_provider, name="add_storage_provider"
    ),
    path(
        "delete_storage_provider/<int:storage_id>/",
        views.delete_storage_provider,
        name="delete_storage_provider",
    ),
    path(
        "edit_storage_provider/<int:storage_id>/",
        views.edit_storage_provider,
        name="edit_storage_provider",
    ),
    path("signup", views.signup, name="signup"),
    path("login", auth_views.LoginView.as_view(), name="login"),
    path("logout", auth_views.LogoutView.as_view(), name="logout"),
    path("admin/", admin.site.urls),
    path("api/", include("backends.urls")),
    path("accounts/", include("allauth.urls")),
]
