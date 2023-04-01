"""Module that defines the user api.
"""
from datetime import datetime
import uuid

import pytz

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.template import loader
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required

from decouple import config

from backends.apps import BackendsConfig as ac
from backends.models import Token

from .forms import SignUpForm
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

    storage_provider = getattr(ac, "storage")
    backend_names = storage_provider.get_backends()
    backend_list = []
    for backend in backend_names:
        # for testing we created dummy devices. We should ignore them in any other cases.
        if not "dummy_" in backend:
            config_dict = storage_provider.get_backend_dict(backend)
            backend_list.append(config_dict)
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
    template = loader.get_template("frontend/user.html")
    context = {"token_key": token.key}
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
