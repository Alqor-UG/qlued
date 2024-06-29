"""Module that defines the user api.
"""

import json
import uuid
from datetime import datetime

import pytz
from decouple import config
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import loader
from django.urls import reverse
from pydantic import ValidationError

from qlued.models import StorageProviderDb, Token
from qlued.storage_providers import (
    get_storage_provider_from_entry,
    get_short_backend_name
)

from .forms import SignUpForm, StorageProviderForm
from .models import Impressum


def index(request):
    """The index view that is called at the beginning."""
    # pylint: disable=E1101
    template = loader.get_template("frontend/index.html")

    current_user = request.user
    context = {}

    if current_user.is_authenticated:
        try:
            token = Token.objects.get(user=current_user)
        except Token.DoesNotExist:
            # create a token if it does not exist yet.
            key = uuid.uuid4().hex
            token = Token.objects.create(
                key=key,
                user=current_user,
                created_at=datetime.now(pytz.utc),
                is_active=True,
            )
            token.save()
        context = {"token_key": token.key}

    return HttpResponse(template.render(context, request))


def devices(request):
    """The about that contains all the available backend devices."""
    template = loader.get_template("frontend/backends.html")

    # pylint: disable=W0613, E1101
    backend_list = []
    # obtain all the available storage providers from the database
    storage_provider_entries = StorageProviderDb.objects.all()

    # now loop through them and obtain the backends
    for storage_provider_entry in storage_provider_entries:
        if not storage_provider_entry.is_active:
            continue
        try:
            storage_provider = get_storage_provider_from_entry(storage_provider_entry)

            backend_names = storage_provider.get_backends()
            for backend in backend_names:
                # for testing we created dummy devices. We should ignore them in any other cases.
                if not "dummy_" in backend:
                    device_status = storage_provider.get_backend_status(backend)
                    # we have to add the URL to the backend configuration
                    base_url = config("BASE_URL")

                    config_dict = device_status.model_dump()
                    config_dict["display_name"] = get_short_backend_name(
                        device_status.backend_name
                    )
                    config_dict["url"] = (
                        base_url + "/api/v2/" + device_status.backend_name + "/"
                    )

                    backend_list.append(config_dict)
        except ValidationError:
            # we ignore the entry if it is not valid
            pass
    base_url = config("BASE_URL", default="http://www.example.com")
    context = {"backend_list": backend_list, "base_url": base_url}
    return HttpResponse(template.render(context, request))


def about(request):
    """The about view that is called for the about page."""
    # pylint: disable=E1101
    template = loader.get_template("frontend/about.html")

    impressums_text = Impressum.objects.first()
    context = {"impressums_text": impressums_text.impressum}
    return HttpResponse(template.render(context, request))


@login_required
def profile(request):
    """
    Given the user an appropiate profile page
    """
    current_user = request.user
    # the use needs to have its token
    try:
        token = Token.objects.get(user=current_user)
    except Token.DoesNotExist:
        # create a token if it does not exist yet.
        key = uuid.uuid4().hex
        token = Token.objects.create(
            key=key,
            user=current_user,
            created_at=datetime.now(pytz.utc),
            is_active=True,
        )
        token.save()

    # we also need to find all the StorageProviderDb entries that belong to the user
    storage_provider_entries = StorageProviderDb.objects.filter(owner=current_user)
    template = loader.get_template("frontend/user.html")
    context = {
        "token_key": token.key,
        "storage_provider_entries": storage_provider_entries,
    }
    return HttpResponse(template.render(context, request))


def signup(request):
    """
    Allow the user to sign up on our website.
    """
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            return HttpResponseRedirect(reverse("profile"))
    else:
        form = SignUpForm()
    return render(request, "frontend/signup.html", {"form": form})


def change_password(request):
    """Function that changes the password.

    Args:
        request: the request to be handled.

    Returns:
        HttpResponse
    """
    if request.method == "POST":
        try:
            username = request.POST["username"]
            password = request.POST["password"]
            new_password = request.POST["new_password"]
            user = authenticate(username=username, password=password)
        except ObjectDoesNotExist:
            return HttpResponse("Unable to get credentials!", status=401)
        if user is not None:
            user.set_password(new_password)
            user.save()
            return HttpResponse("Password changed!")
        return HttpResponse("Invalid credentials!", status=401)
    return HttpResponse("Only POST request allowed!", 405)


@login_required
def add_storage_provider(request):
    """Function that allows the user to register a new storage provider.

    Args:
        request: the request to be handled.

    Returns:
        HttpResponse
    """
    if request.method == "POST":
        form = StorageProviderForm(request.POST)
        if form.is_valid():
            storage_type = request.POST["storage_type"]
            name = request.POST["name"]
            description = request.POST["description"]
            login_string = request.POST["login"]

            # the current user is the owner of the storage provider
            owner = request.user
            storage_provider = StorageProviderDb(
                storage_type=storage_type,
                name=name,
                is_active=True,
                owner=owner,
                description=description,
                login=json.loads(login_string),
            )
            storage_provider.full_clean()
            storage_provider.save()
            return HttpResponseRedirect(reverse("profile"))
    else:
        form = StorageProviderForm()
    return render(request, "frontend/add_storage_provider.html", {"form": form})


@login_required
def edit_storage_provider(request, storage_id):
    """Function that allows the owner to edit an existing storage provider.

    Args:
        request: the request to be handled.
        storage_id: the id of the storage provider to be edited.

    Returns:
        HttpResponse
    """
    if request.method == "POST":
        try:
            storage_provider = StorageProviderDb.objects.get(id=storage_id)
        except ObjectDoesNotExist:
            return HttpResponse("Storage provider does not exist!", status=404)
        # check if the user is the owner of the storage provider
        if storage_provider.owner != request.user:
            return HttpResponse(
                "You are not the owner of the storage provider!", status=401
            )
        form = StorageProviderForm(request.POST, instance=storage_provider)
        if form.is_valid():
            storage_provider.storage_type = request.POST["storage_type"]
            storage_provider.name = request.POST["name"]
            storage_provider.description = request.POST["description"]
            storage_provider.login = json.loads(request.POST["login"])

            # get the is_active field
            # this is really ugly but I don't know how to do it better
            active_value = request.POST.get("is_active", False)
            if not active_value:
                storage_provider.is_active = False
            else:
                storage_provider.is_active = request.POST["is_active"] == "on"

            # now clean the storage provider and save it
            storage_provider.full_clean()
            storage_provider.save()
            return HttpResponseRedirect(reverse("profile"))
    else:
        try:
            storage_provider = StorageProviderDb.objects.get(id=storage_id)
        except ObjectDoesNotExist:
            return HttpResponse("Storage provider does not exist!", status=404)
        # check if the user is the owner of the storage provider
        if storage_provider.owner != request.user:
            return HttpResponse(
                "You are not the owner of the storage provider!", status=401
            )
        form = StorageProviderForm(
            initial={
                "storage_type": storage_provider.storage_type,
                "name": storage_provider.name,
                "description": storage_provider.description,
                "login": storage_provider.login,
                "is_active": storage_provider.is_active,
            }
        )
    return render(
        request,
        "frontend/edit_storage_provider.html",
        {"form": form, "storage_id": storage_id},
    )


@login_required
def delete_storage_provider(request, storage_id):
    """Function that allows the owner to remove a storage provider.

    Args:
        request: the request to be handled.
        storage_id: the id of the storage provider to be deleted.
    """
    if request.method in ("POST", "GET"):
        try:
            storage_provider = StorageProviderDb.objects.get(id=storage_id)
        except ObjectDoesNotExist:
            return HttpResponse("Storage provider does not exist!", status=404)
        # check if the user is the owner of the storage provider
        if storage_provider.owner != request.user:
            return HttpResponse(
                "You are not the owner of the storage provider!", status=401
            )
    else:
        return HttpResponse("Only POST and GET request allowed!", 405)

    # delete the storage provider from the database if the user confirmed the deletion
    if request.method == "POST":
        storage_provider.delete()
        return HttpResponseRedirect(reverse("profile"))

    # show the user a confirmation page
    return render(
        request,
        "frontend/delete_storage_provider.html",
        {"storage_provider": storage_provider},
    )
